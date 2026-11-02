"""
DELETE /api/organizations/{id} (B16, issue #145).

Every test runs on SQLite and on a throwaway PostgreSQL database (`engine`
fixture in conftest.py). The row-by-row checks of the purge itself are in
test_purge_organization.py; here: the endpoint, its permissions, the name
confirmation, the files and the rollback.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.app_config import app_settings
from app.core.database import get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.alerts.model import Alert
from app.modules.documents import storage
from app.modules.documents.model import Document
from app.modules.invitations.model import Invitation
from app.modules.organizations import service as organization_service
from app.modules.organizations.model import Organization
from app.modules.organizations.service import OrganizationService
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------
# Data: organization A (deleted) and B (must survive untouched)
# ---------------------------------------------------------
def _organization(db: Session, name: str) -> dict:
    org = Organization(name=name)
    db.add(org)
    db.flush()
    client = User(
        organization_id=org.id,
        email=f"client@{name.lower().replace(' ', '')}.test",
        name="Client",
        password_hash="hashed",
        role="client",
    )
    site = Site(organization_id=org.id, name=f"Edificio {name}")
    db.add_all([client, site])
    db.flush()
    sensor = Sensor(
        site_id=site.id,
        external_id=f"S-{name}",
        name="Sensor",
        low_threshold=Decimal("1.5"),
        high_threshold=Decimal("6"),
    )
    db.add(sensor)
    db.flush()
    db.add_all(
        Reading(
            sensor_id=sensor.id,
            value=Decimal("3.5"),
            unit="bar",
            recorded_at=NOW - timedelta(minutes=i),
        )
        for i in range(5)
    )
    db.add_all(
        [
            Alert(
                sensor_id=sensor.id,
                alert_type="LOW_PRESSURE",
                status="ACTIVE",
                severity="WARNING",
                message="Presión baja",
            ),
            Document(
                organization_id=org.id,
                site_id=site.id,
                kind="PLAN",
                filename="plano.pdf",
                content_type="application/pdf",
                size=4,
                storage_key=f"{org.id}/plano.pdf",
                uploaded_by=client.id,
            ),
            Invitation(
                organization_id=org.id,
                email=f"nuevo@{name.lower().replace(' ', '')}.test",
                code_hash=f"hash-{name}",
                expires_at=NOW + timedelta(days=7),
                created_by=client.id,
            ),
        ]
    )
    db.flush()
    return {"org": org, "client": client}


@pytest.fixture()
def documents_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(app_settings, "DOCUMENTS_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def data(engine, documents_dir):
    with Session(engine, expire_on_commit=False) as db:
        a = _organization(db, "Hotel Sol")
        b = _organization(db, "Colegio Luna")
        admin = User(
            organization_id=None,
            email="admin@test.test",
            name="Admin",
            password_hash="hashed",
            role="admin",
        )
        # An admin assigned to A: must survive, detached.
        admin_of_a = User(
            organization_id=a["org"].id,
            email="admin-a@test.test",
            name="Admin A",
            password_hash="hashed",
            role="admin",
        )
        db.add_all([admin, admin_of_a])
        db.commit()

    # The files of both organizations' documents.
    for org in (a["org"], b["org"]):
        folder = documents_dir / str(org.id)
        folder.mkdir()
        (folder / "plano.pdf").write_bytes(b"%PDF")

    return {"a": a, "b": b, "admin": admin, "admin_of_a": admin_of_a}


@pytest.fixture()
def client(engine):
    def _get_db():
        db = Session(engine, expire_on_commit=False)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def _login(client, user):
    client.cookies.set(SESSION_COOKIE, create_session_token(user.id))


def _delete(client, org_id, confirm_name):
    return client.request(
        "DELETE",
        f"/api/organizations/{org_id}",
        json={"confirm_name": confirm_name},
    )


def _count(engine, model, *where) -> int:
    with Session(engine) as db:
        return db.scalar(select(func.count()).select_from(model).where(*where))


def _rows_of(engine, org_id) -> int:
    """Every row that hangs from the organization, in any table."""
    with Session(engine) as db:
        sites = select(Site.id).where(Site.organization_id == org_id)
        sensors = select(Sensor.id).where(Sensor.site_id.in_(sites))
        checks = [
            (Organization, Organization.id == org_id),
            (Site, Site.organization_id == org_id),
            (Sensor, Sensor.site_id.in_(sites)),
            (Reading, Reading.sensor_id.in_(sensors)),
            (Alert, Alert.sensor_id.in_(sensors)),
            (Document, Document.organization_id == org_id),
            (Invitation, Invitation.organization_id == org_id),
            (User, User.organization_id == org_id),
        ]
        return sum(
            db.scalar(select(func.count()).select_from(model).where(where))
            for model, where in checks
        )


# ---------------------------------------------------------
# Admin deletes
# ---------------------------------------------------------
def test_admin_deletes_the_organization_with_all_its_data(engine, data, client, documents_dir):
    a, b = data["a"]["org"], data["b"]["org"]
    rows_of_b = _rows_of(engine, b.id)
    _login(client, data["admin"])

    response = _delete(client, a.id, "Hotel Sol")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(a.id)
    assert body["name"] == "Hotel Sol"
    assert body["deleted"] == {
        "readings": 5,
        "alerts": 1,
        "sensors": 1,
        "documents": 1,
        "sites": 1,
        "invitations": 1,
        "users": 1,
        "organizations": 1,
    }
    assert body["detached_admins"] == 1
    assert body["deleted_files"] == 1

    # Nothing of A is left, B is untouched.
    assert _rows_of(engine, a.id) == 0
    assert _rows_of(engine, b.id) == rows_of_b
    assert not (documents_dir / str(a.id) / "plano.pdf").exists()
    assert (documents_dir / str(b.id) / "plano.pdf").exists()

    # The admin of A survives, without organization.
    with Session(engine) as db:
        admin_of_a = db.get(User, data["admin_of_a"].id)
        assert admin_of_a is not None
        assert admin_of_a.organization_id is None

    assert client.get(f"/api/organizations/{a.id}").status_code == 404


def test_confirm_name_ignores_surrounding_spaces(engine, data, client):
    _login(client, data["admin"])

    response = _delete(client, data["a"]["org"].id, "  Hotel Sol  ")

    assert response.status_code == 200


def test_a_document_without_file_does_not_fail(engine, data, client, documents_dir):
    (documents_dir / str(data["a"]["org"].id) / "plano.pdf").unlink()
    _login(client, data["admin"])

    response = _delete(client, data["a"]["org"].id, "Hotel Sol")

    assert response.status_code == 200
    assert response.json()["deleted_files"] == 0
    assert _rows_of(engine, data["a"]["org"].id) == 0


# ---------------------------------------------------------
# Refused: nothing is deleted
# ---------------------------------------------------------
@pytest.mark.parametrize("confirm_name", ["hotel sol", "Hotel", "Colegio Luna", ""])
def test_wrong_name_is_refused(engine, data, client, confirm_name):
    a = data["a"]["org"]
    rows = _rows_of(engine, a.id)
    _login(client, data["admin"])

    response = _delete(client, a.id, confirm_name)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "NAME_CONFIRMATION_MISMATCH"
    assert _rows_of(engine, a.id) == rows


def test_without_confirm_name_is_refused(engine, data, client):
    _login(client, data["admin"])

    response = client.request("DELETE", f"/api/organizations/{data['a']['org'].id}")

    assert response.status_code == 422
    assert _count(engine, Organization) == 2


def test_unknown_organization_is_404(engine, data, client):
    _login(client, data["admin"])

    response = _delete(client, uuid.uuid4(), "Hotel Sol")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ORGANIZATION_NOT_FOUND"


def test_a_client_cannot_delete_organizations(engine, data, client, documents_dir):
    a = data["a"]["org"]
    rows = _rows_of(engine, a.id)
    _login(client, data["a"]["client"])

    response = _delete(client, a.id, "Hotel Sol")

    assert response.status_code == 403
    assert _rows_of(engine, a.id) == rows
    assert (documents_dir / str(a.id) / "plano.pdf").exists()


def test_without_session_is_401(engine, data, client):
    response = _delete(client, data["a"]["org"].id, "Hotel Sol")

    assert response.status_code == 401
    assert _count(engine, Organization) == 2


# ---------------------------------------------------------
# One transaction: a failure deletes nothing, not even the files
# ---------------------------------------------------------
def test_a_failure_mid_purge_rolls_everything_back(engine, data, documents_dir, monkeypatch):
    a = data["a"]["org"]
    rows = _rows_of(engine, a.id)
    real_purge = organization_service.purge_organization

    def failing_purge(db, organization_id):
        real_purge(db, organization_id)  # deletes every row...
        raise RuntimeError("database down")  # ...and then fails before the commit

    monkeypatch.setattr(organization_service, "purge_organization", failing_purge)

    with Session(engine, expire_on_commit=False) as db:
        with pytest.raises(RuntimeError):
            OrganizationService(db).delete(a.id, "Hotel Sol")

    assert _rows_of(engine, a.id) == rows
    assert (documents_dir / str(a.id) / "plano.pdf").exists()


# ---------------------------------------------------------
# Files
# ---------------------------------------------------------
def test_delete_files_never_leaves_the_documents_folder(tmp_path):
    root = tmp_path / "documents"
    root.mkdir()
    outside = tmp_path / "secret.txt"
    outside.write_text("keep me")
    (root / "ok.pdf").write_bytes(b"%PDF")

    deleted = storage.delete_files(["ok.pdf", "../secret.txt", "missing.pdf"], root=root)

    assert deleted == 1
    assert not (root / "ok.pdf").exists()
    assert outside.exists()
