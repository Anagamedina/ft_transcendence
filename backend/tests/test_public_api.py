"""Contrato y aislamiento de la API pública del subject (lectura y escritura)."""

from datetime import datetime, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra todas las entidades ORM
from app.core.app_config import app_settings
from app.core.database import Base, get_db
from app.main import app
from app.modules.alerts.model import Alert
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site


API_KEY = "test-public-api-key"
WRITE_KEY = "test-public-api-write-key"
PERIOD_START = datetime(2026, 9, 1, tzinfo=timezone.utc)
PERIOD_END = datetime(2026, 10, 1, tzinfo=timezone.utc)


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def data(engine, monkeypatch):
    with Session(engine, expire_on_commit=False) as session:
        org_a = Organization(name="API Cliente A")
        org_b = Organization(name="API Cliente B")
        session.add_all([org_a, org_b])
        session.flush()

        site_a = Site(organization_id=org_a.id, name="Edificio A")
        site_b = Site(organization_id=org_b.id, name="Edificio B")
        session.add_all([site_a, site_b])
        session.flush()

        sensor_a = Sensor(
            site_id=site_a.id,
            external_id="API-A-1",
            name="Sensor A",
            unit="bar",
            low_threshold=Decimal("1.000"),
            high_threshold=Decimal("8.000"),
        )
        sensor_b = Sensor(
            site_id=site_b.id,
            external_id="API-B-1",
            name="Sensor B",
            unit="bar",
            low_threshold=Decimal("1.000"),
            high_threshold=Decimal("8.000"),
        )
        session.add_all([sensor_a, sensor_b])
        session.flush()

        session.add_all(
            [
                Reading(
                    sensor_id=sensor_a.id,
                    value=Decimal("3.500"),
                    unit="bar",
                    recorded_at=datetime(2026, 9, 15, 10, tzinfo=timezone.utc),
                    created_at=datetime(2026, 9, 15, 10, tzinfo=timezone.utc),
                ),
                Alert(
                    sensor_id=sensor_a.id,
                    alert_type="LOW_PRESSURE",
                    status="ACTIVE",
                    severity="WARNING",
                    message="Presión baja en A",
                    created_at=datetime(2026, 9, 15, 11, tzinfo=timezone.utc),
                ),
            ]
        )
        session.commit()

        monkeypatch.setattr(app_settings, "PUBLIC_API_KEY", API_KEY)
        monkeypatch.setattr(app_settings, "PUBLIC_API_WRITE_KEY", WRITE_KEY)
        monkeypatch.setattr(app_settings, "PUBLIC_API_ORGANIZATION_ID", org_a.id)
        return {
            "a": org_a,
            "b": org_b,
            "site_a": site_a,
            "site_b": site_b,
            "sensor_b": sensor_b,
        }


@pytest.fixture()
def client(engine):
    def _get_db():
        db = Session(engine, expire_on_commit=False)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    test_client = TestClient(app)
    yield test_client
    test_client.close()
    app.dependency_overrides.clear()


def headers(key=API_KEY):
    return {"X-API-Key": key} if key is not None else {}


def test_public_api_requires_a_dedicated_key(client, data):
    assert client.get("/api/public/v1/overview").status_code == 401
    wrong = client.get("/api/public/v1/overview", headers=headers("wrong"))
    assert wrong.status_code == 401
    assert wrong.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize(
    "path",
    [
        "/api/public/v1/overview",
        "/api/public/v1/sites",
        "/api/public/v1/sensors",
        "/api/public/v1/alerts",
        "/api/public/v1/analytics/export?from=2026-09-01&to=2026-10-01",
    ],
)
def test_public_api_exposes_the_read_endpoints(client, data, path):
    response = client.get(path, headers=headers())
    assert response.status_code == 200, response.text


def test_public_api_is_scoped_to_the_configured_organization(client, data):
    sites = client.get("/api/public/v1/sites", headers=headers()).json()
    sensors = client.get("/api/public/v1/sensors", headers=headers()).json()
    alerts = client.get("/api/public/v1/alerts", headers=headers()).json()

    assert [item["name"] for item in sites["items"]] == ["Edificio A"]
    assert [item["external_id"] for item in sensors["items"]] == ["API-A-1"]
    assert all(item["organization_id"] == str(data["a"].id) for item in alerts["items"])
    assert str(data["b"].id) not in str(sites)
    assert "API-B-1" not in str(sensors)


NEW_SITE = {
    "name": "Edificio Nuevo",
    "address": "Carrer de Mallorca, 1",
    "latitude": 41.39,
    "longitude": 2.16,
    "floors": 4,
    "basements": 1,
    "building_type": "OFFICE",
}


def _sites_of(engine, organization_id):
    with Session(engine) as session:
        return {
            site.name
            for site in session.query(Site).filter_by(organization_id=organization_id)
        }


# ---------------------------------------------------------
# Escritura: crear, ver, reemplazar y borrar edificios
# ---------------------------------------------------------
def test_write_key_creates_reads_replaces_and_deletes_a_site(client, data, engine):
    created = client.post(
        "/api/public/v1/sites", headers=headers(WRITE_KEY), json=NEW_SITE
    )
    assert created.status_code == 201, created.text
    site = created.json()
    assert site["organization_id"] == str(data["a"].id)
    assert site["floors"] == 4

    read = client.get(f"/api/public/v1/sites/{site['id']}", headers=headers())
    assert read.status_code == 200
    assert read.json()["name"] == "Edificio Nuevo"

    replaced = client.put(
        f"/api/public/v1/sites/{site['id']}",
        headers=headers(WRITE_KEY),
        json={"name": "Edificio Renombrado", "floors": 2},
    )
    assert replaced.status_code == 200, replaced.text
    body = replaced.json()
    assert body["name"] == "Edificio Renombrado"
    assert body["floors"] == 2
    # PUT reemplaza: lo que no se envía vuelve a su valor por defecto
    assert body["address"] is None
    assert body["basements"] == 0
    assert body["building_type"] == "OTHER"

    deleted = client.delete(
        f"/api/public/v1/sites/{site['id']}", headers=headers(WRITE_KEY)
    )
    assert deleted.status_code == 204
    assert _sites_of(engine, data["a"].id) == {"Edificio A"}


def test_write_key_also_reads(client, data):
    response = client.get("/api/public/v1/overview", headers=headers(WRITE_KEY))
    assert response.status_code == 200


@pytest.mark.parametrize(
    "method, path",
    [
        ("post", "/api/public/v1/sites"),
        ("put", "/api/public/v1/sites/{site}"),
        ("delete", "/api/public/v1/sites/{site}"),
    ],
)
def test_read_key_cannot_write(client, data, engine, method, path):
    url = path.format(site=data["site_a"].id)
    kwargs = {"json": NEW_SITE} if method != "delete" else {}
    response = getattr(client, method)(url, headers=headers(), **kwargs)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "PUBLIC_API_READ_ONLY"
    assert _sites_of(engine, data["a"].id) == {"Edificio A"}


@pytest.mark.parametrize("key", [None, "wrong"])
def test_writing_without_a_valid_key_gives_401(client, data, key):
    response = client.post(
        "/api/public/v1/sites", headers=headers(key), json=NEW_SITE
    )
    assert response.status_code == 401


def test_writes_are_off_when_the_write_key_is_empty(client, data, monkeypatch):
    monkeypatch.setattr(app_settings, "PUBLIC_API_WRITE_KEY", "")

    empty = client.post("/api/public/v1/sites", headers=headers(""), json=NEW_SITE)
    read_key = client.post("/api/public/v1/sites", headers=headers(), json=NEW_SITE)

    assert empty.status_code == 401
    assert read_key.status_code == 403


def test_the_body_cannot_choose_another_organization(client, data, engine):
    response = client.post(
        "/api/public/v1/sites",
        headers=headers(WRITE_KEY),
        json={**NEW_SITE, "organization_id": str(data["b"].id)},
    )
    assert response.status_code == 422
    assert _sites_of(engine, data["b"].id) == {"Edificio B"}


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_a_site_of_another_organization_is_not_found(client, data, engine, method):
    url = f"/api/public/v1/sites/{data['site_b'].id}"
    key = API_KEY if method == "get" else WRITE_KEY
    kwargs = {"json": NEW_SITE} if method == "put" else {}
    response = getattr(client, method)(url, headers=headers(key), **kwargs)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "SITE_NOT_FOUND"
    assert _sites_of(engine, data["b"].id) == {"Edificio B"}


def test_a_duplicated_name_gives_409(client, data):
    response = client.post(
        "/api/public/v1/sites",
        headers=headers(WRITE_KEY),
        json={**NEW_SITE, "name": "Edificio A"},
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SITE_NAME_TAKEN"


def test_a_site_with_sensors_is_not_deleted(client, data, engine):
    with Session(engine) as session:
        session.add(
            Sensor(
                site_id=data["site_a"].id,
                external_id="API-A-2",
                name="Sensor A2",
                unit="bar",
                low_threshold=Decimal("1.000"),
                high_threshold=Decimal("8.000"),
            )
        )
        session.commit()

    response = client.delete(
        f"/api/public/v1/sites/{data['site_a'].id}", headers=headers(WRITE_KEY)
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SITE_HAS_SENSORS"


def test_the_site_limit_of_the_contract_applies(client, data, engine):
    """En prueba solo cabe un edificio, y la organización A ya lo tiene."""
    with Session(engine) as session:
        organization = session.get(Organization, data["a"].id)
        organization.status = "TRIAL"
        session.commit()

    response = client.post(
        "/api/public/v1/sites", headers=headers(WRITE_KEY), json=NEW_SITE
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "SITE_LIMIT_REACHED"


def test_an_expired_trial_reads_but_does_not_write(client, data, engine):
    with Session(engine) as session:
        organization = session.get(Organization, data["a"].id)
        organization.status = "TRIAL"
        organization.trial_ends_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        session.commit()

    read = client.get("/api/public/v1/sites", headers=headers(WRITE_KEY))
    write = client.delete(
        f"/api/public/v1/sites/{data['site_a'].id}", headers=headers(WRITE_KEY)
    )

    assert read.status_code == 200
    assert write.status_code == 403
    assert write.json()["error"]["code"] == "TRIAL_EXPIRED"
    assert _sites_of(engine, data["a"].id) == {"Edificio A"}


def test_a_suspended_organization_cannot_use_the_api(client, data, engine):
    with Session(engine) as session:
        session.get(Organization, data["a"].id).status = "SUSPENDED"
        session.commit()

    response = client.get("/api/public/v1/sites", headers=headers())
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ACCOUNT_DISABLED"


def test_patch_is_not_part_of_the_public_api(client, data):
    response = client.patch(
        f"/api/public/v1/sites/{data['site_a'].id}",
        headers=headers(WRITE_KEY),
        json={"name": "x"},
    )
    assert response.status_code == 405


def test_public_api_declares_api_key_security_and_all_paths(client, data):
    document = client.get("/api/openapi.json").json()
    paths = document["paths"]
    expected = {
        "/api/public/v1/overview",
        "/api/public/v1/sites",
        "/api/public/v1/sensors",
        "/api/public/v1/alerts",
        "/api/public/v1/analytics/export",
    }
    assert expected <= paths.keys()
    assert "PublicApiKey" in document["components"]["securitySchemes"]
    assert all("security" in paths[path]["get"] for path in expected)

    site = paths["/api/public/v1/sites/{site_id}"]
    assert {"get", "put", "delete"} <= site.keys()
    assert "post" in paths["/api/public/v1/sites"]
    assert all("security" in operation for operation in site.values())
