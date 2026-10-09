"""
purge_organization (D9, issue #133).

Every test runs twice: on SQLite (foreign keys on) and on PostgreSQL. The
PostgreSQL run creates a throwaway database next to the dev one, builds the
schema there and drops it at the end; the dev data is never touched. It is
skipped when PostgreSQL is not reachable (tests run outside Docker), so run
it inside the stack:

    docker compose run --rm --no-deps -v "$PWD/backend:/src" \\
        --entrypoint sh backend -c "cd /src && python -m pytest tests/integration"

The schema comes from the models (create_all). It matches the migrations
because `make migration-check` fails on any drift.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core import models  # noqa: F401 - registers the ORM models
from app.core.config import settings
from app.core.database import Base, transaction
from app.modules.alerts.model import Alert
from app.modules.documents.model import Document
from app.modules.invitations.model import Invitation
from app.modules.organizations.model import Organization
from app.modules.organizations.purge import purge_organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

NOW = datetime.now(timezone.utc)
READINGS_PER_SENSOR = 50


# ---------------------------------------------------------
# Engines
# ---------------------------------------------------------
def _sqlite_engine():
    engine = create_engine("sqlite+pysqlite:///:memory:")

    @event.listens_for(engine, "connect")
    def _foreign_keys_on(dbapi_connection, _record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    return engine, lambda: engine.dispose()


def _postgres_engine():
    admin = create_engine(
        settings.DATABASE_URL,
        isolation_level="AUTOCOMMIT",
        connect_args={"connect_timeout": 3},
    )
    try:
        admin.connect().close()
    except OperationalError:
        admin.dispose()
        pytest.skip("PostgreSQL is not reachable; run the tests inside the stack")

    name = f"aquaguard_test_purge_{uuid.uuid4().hex[:8]}"
    with admin.connect() as connection:
        connection.execute(text(f'CREATE DATABASE "{name}"'))
    engine = create_engine(make_url(settings.DATABASE_URL).set(database=name))
    Base.metadata.create_all(engine)

    def _drop():
        engine.dispose()
        with admin.connect() as connection:
            connection.execute(text(f'DROP DATABASE "{name}" WITH (FORCE)'))
        admin.dispose()

    return engine, _drop


@pytest.fixture(params=["sqlite", "postgresql"])
def engine(request):
    engine, cleanup = (
        _sqlite_engine() if request.param == "sqlite" else _postgres_engine()
    )
    yield engine
    cleanup()


# ---------------------------------------------------------
# Data: organization A (purged) and B (must survive untouched)
# ---------------------------------------------------------
def _organization(db: Session, name: str) -> dict:
    org = Organization(name=name)
    db.add(org)
    db.flush()
    client = User(
        organization_id=org.id,
        email=f"client@{name.lower()}.test",
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
        for i in range(READINGS_PER_SENSOR)
    )
    alert = Alert(
        sensor_id=sensor.id,
        alert_type="LOW_PRESSURE",
        status="RESOLVED",
        severity="WARNING",
        message="Presión baja",
        acknowledged_by=client.id,
        resolved_by=client.id,
    )
    document = Document(
        organization_id=org.id,
        site_id=site.id,
        kind="PLAN",
        filename="plano.pdf",
        content_type="application/pdf",
        size=1024,
        storage_key=f"{name}/plano.pdf",
        uploaded_by=client.id,
    )
    invitation = Invitation(
        organization_id=org.id,
        email=f"nuevo@{name.lower()}.test",
        code_hash=f"hash-{name}",
        expires_at=NOW + timedelta(days=7),
        created_by=client.id,
    )
    db.add_all([alert, document, invitation])
    db.flush()
    return {"org": org, "client": client, "alert": alert, "document": document}


@pytest.fixture()
def data(engine):
    with Session(engine, expire_on_commit=False) as db:
        a = _organization(db, "A")
        b = _organization(db, "B")
        # An admin attached to A who handled an alert of B.
        admin_of_a = User(
            organization_id=a["org"].id,
            email="admin@a.test",
            name="Admin A",
            password_hash="hashed",
            role="admin",
        )
        db.add(admin_of_a)
        db.flush()
        b["alert"].acknowledged_by = admin_of_a.id
        # A client of A who uploaded a document of B (cross reference).
        b["document"].uploaded_by = a["client"].id
        db.commit()
        return {"a": a, "b": b, "admin_of_a": admin_of_a}


def _purge(engine, organization_id):
    with Session(engine) as db:
        with transaction(db):
            return purge_organization(db, organization_id)


def _count(db: Session, model, *where) -> int:
    return db.scalar(select(func.count()).select_from(model).where(*where))


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------
def test_purge_deletes_everything_of_the_organization(engine, data):
    org_id = data["a"]["org"].id

    result = _purge(engine, org_id)

    assert result.deleted == {
        "readings": READINGS_PER_SENSOR,
        "alerts": 1,
        "sensors": 1,
        "documents": 1,
        "sites": 1,
        "invitations": 1,
        "users": 1,
        "organizations": 1,
    }
    with Session(engine) as db:
        assert db.get(Organization, org_id) is None
        assert _count(db, Site, Site.organization_id == org_id) == 0
        assert _count(db, User, User.organization_id == org_id) == 0
        assert _count(db, Document, Document.organization_id == org_id) == 0
        assert _count(db, Invitation, Invitation.organization_id == org_id) == 0


def test_no_orphan_rows_are_left(engine, data):
    _purge(engine, data["a"]["org"].id)

    with Session(engine) as db:
        site_ids = select(Site.id)
        sensor_ids = select(Sensor.id)
        org_ids = select(Organization.id)
        assert _count(db, Sensor, Sensor.site_id.not_in(site_ids)) == 0
        assert _count(db, Reading, Reading.sensor_id.not_in(sensor_ids)) == 0
        assert _count(db, Alert, Alert.sensor_id.not_in(sensor_ids)) == 0
        assert _count(db, Document, Document.site_id.not_in(site_ids)) == 0
        assert _count(db, Document, Document.organization_id.not_in(org_ids)) == 0
        assert _count(db, Invitation, Invitation.organization_id.not_in(org_ids)) == 0
        assert _count(db, User, User.organization_id.not_in(org_ids)) == 0


def test_the_other_organization_is_untouched(engine, data):
    b = data["b"]

    _purge(engine, data["a"]["org"].id)

    with Session(engine) as db:
        assert db.get(Organization, b["org"].id) is not None
        assert _count(db, Reading) == READINGS_PER_SENSOR
        assert _count(db, Alert) == 1
        assert _count(db, Sensor) == 1
        assert _count(db, Document) == 1
        assert _count(db, Invitation) == 1
        # References from B to deleted users of A become NULL.
        assert db.get(Document, b["document"].id).uploaded_by is None


def test_admins_are_detached_not_deleted(engine, data):
    admin_id = data["admin_of_a"].id

    result = _purge(engine, data["a"]["org"].id)

    assert result.detached_admins == 1
    with Session(engine) as db:
        admin = db.get(User, admin_id)
        assert admin is not None
        assert admin.organization_id is None
        # The alert of B that this admin acknowledged keeps its actor.
        assert db.get(Alert, data["b"]["alert"].id).acknowledged_by == admin_id


def test_unknown_organization_returns_none(engine, data):
    assert _purge(engine, uuid.uuid4()) is None


def test_a_failure_rolls_everything_back(engine, data, monkeypatch):
    """One transaction: if the last DELETE fails, nothing is deleted."""
    org_id = data["a"]["org"].id
    real_execute = Session.execute

    def _fail_on_organization_delete(self, statement, *args, **kwargs):
        if getattr(statement, "is_delete", False) and statement.table.name == "organizations":
            raise RuntimeError("simulated failure")
        return real_execute(self, statement, *args, **kwargs)

    monkeypatch.setattr(Session, "execute", _fail_on_organization_delete)
    with pytest.raises(RuntimeError):
        _purge(engine, org_id)
    monkeypatch.undo()

    with Session(engine) as db:
        assert db.get(Organization, org_id) is not None
        assert _count(db, Reading) == 2 * READINGS_PER_SENSOR
        assert _count(db, Site) == 2
