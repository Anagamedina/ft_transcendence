"""Contrato y aislamiento de la API pública read-only del subject."""

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
        monkeypatch.setattr(app_settings, "PUBLIC_API_ORGANIZATION_ID", org_a.id)
        return {"a": org_a, "b": org_b, "site_b": site_b, "sensor_b": sensor_b}


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
def test_public_api_exposes_five_read_only_endpoints(client, data, path):
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


def test_public_api_does_not_accept_sessionless_write_operations(client, data):
    response = client.post("/api/public/v1/sites", headers=headers(), json={})
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
