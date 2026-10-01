"""Read-only source audit probes against a disposable PostgreSQL database.

Run from backend/ with POSTGRES_* pointing ONLY at an empty audit database.
The script applies migrations and inserts demo data into that audit database.
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.core.config import settings
from app.core import models
from app.core.database import get_db
from app.main import app
from app.modules.users.model import User
from app.modules.sensors.model import Sensor
from app.modules.sensors.schemas import SensorResponse
from app.modules.readings.service import ReadingService
from app.modules.readings.schemas import ReadingCreate
from app.modules.readings.repository import ReadingRepository
from app.modules.sensors.repository import SensorRepository
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.model import Alert
from app.core.exceptions import ConflictError
from seeds import seed_demo

assert settings.POSTGRES_DB == "audit", "Use the disposable audit database only"
assert settings.POSTGRES_HOST == "127.0.0.1" and settings.POSTGRES_PORT == 55439
assert settings.POSTGRES_USER == "audit" and settings.POSTGRES_PASSWORD == "audit-local-only"
results = {}
config = Config("alembic.ini")
command.upgrade(config, "head")
results["upgrade_empty_database"] = "PASS"
command.check(config)
results["alembic_check_current_models"] = "PASS"
seed_demo.seed()
engine = create_engine(settings.DATABASE_URL)

def override_db():
    with Session(engine, expire_on_commit=False) as db:
        yield db

app.dependency_overrides[get_db] = override_db
try:
    with TestClient(app) as client:
        login = client.post("/api/auth/login", json={"email": "admin@aquaguard.dev", "password": "dev-admin-only"})
        results["seed_admin_login"] = login.status_code
        created = client.post("/api/auth/register", json={"email": f"probe-{uuid4()}@example.com", "name": "Audit Client", "password": "audit-password"})
        results["global_admin_register"] = {"status": created.status_code, "organization_id": created.json().get("user", {}).get("organization_id")}
        results["global_admin_alerts"] = client.get("/api/alerts").json()
        results["sites_route"] = client.get("/api/sites").status_code
        results["sensors_route"] = client.get("/api/sensors").status_code
        sensor_id = "00000000-0000-4000-8000-000000000001"
        payload = {"id": str(uuid4()), "sensor_id": sensor_id, "pressure": 1.2345, "measured_at": "2026-09-30T12:00:00Z"}
        first = client.post("/api/readings", json=payload)
        second = client.post("/api/readings", json=payload)
        with Session(engine) as probe_db:
            stored_value = probe_db.execute(text("SELECT value FROM readings WHERE id = :id"), {"id": payload["id"]}).scalar_one()
        results["rounding_retry"] = {"first_status": first.status_code, "first_response_pressure": first.json().get("pressure"), "database_value": str(stored_value), "retry_status": second.status_code, "retry_error": second.json().get("error", {}).get("code")}
finally:
    app.dependency_overrides.clear()

with Session(engine) as db:
    sensor = db.scalar(select(Sensor))
    try:
        SensorResponse.model_validate(sensor)
    except Exception as exc:
        results["sensor_response_from_orm_missing_fields"] = [e["loc"][0] for e in exc.errors()]
    results["sensor_protocol_last_seen_missing"] = not hasattr(SensorRepository(db), "touch_last_seen")

with Session(engine) as preparation:
    demo = preparation.scalar(select(Sensor))
    audit_sensor = Sensor(id=uuid4(), site_id=demo.site_id, external_id=f"audit-{uuid4()}", name="Audit concurrency", unit="bar")
    sensor_id = audit_sensor.id
    preparation.add(audit_sensor)
    preparation.commit()
with Session(engine) as first, Session(engine) as second:
    # Two sessions observe no offline alert; no unique constraint protects this.
    repo1, repo2 = AlertRepository(first), AlertRepository(second)
    assert repo1.get_active(sensor_id, "SENSOR_OFFLINE") is None
    assert repo2.get_active(sensor_id, "SENSOR_OFFLINE") is None
    repo1.create(sensor_id, "SENSOR_OFFLINE", "WARNING", "audit first")
    first.commit()
    repo2.create(sensor_id, "SENSOR_OFFLINE", "WARNING", "audit second")
    second.commit()
    results["duplicate_active_alerts_allowed"] = len(first.scalars(select(Alert).where(Alert.sensor_id == sensor_id, Alert.alert_type == "SENSOR_OFFLINE", Alert.status == "ACTIVE")).all())

# Percent-encoded credentials are valid URLs but ConfigParser needs %%.
try:
    Config().set_main_option("sqlalchemy.url", "postgresql+psycopg://audit:p%40ss@localhost/audit")
except ValueError as exc:
    results["alembic_percent_encoded_password"] = str(exc)

# Exercise old published migrations with data, in a second disposable DB.
legacy_name = "audit_legacy_" + uuid4().hex[:8]
with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
    connection.execute(text(f"CREATE DATABASE {legacy_name}"))
legacy_engine = create_engine(make_url(settings.DATABASE_URL).set(database=legacy_name))
settings.POSTGRES_DB = legacy_name
legacy_config = Config("alembic.ini")
command.upgrade(legacy_config, "713aa912ec73")
with legacy_engine.begin() as connection:
    org = connection.execute(text("INSERT INTO organizations(name) VALUES ('Legacy') RETURNING id")).scalar_one()
    site = connection.execute(text("INSERT INTO sites(organization_id,name) VALUES (:org,'Legacy') RETURNING id"), {"org": org}).scalar_one()
    sensor = connection.execute(text("INSERT INTO sensors(site_id,external_id,name,unit) VALUES (:site,'legacy','Legacy','bar') RETURNING id"), {"site": site}).scalar_one()
    connection.execute(text("INSERT INTO alerts(sensor_id,alert_type,status,severity) VALUES (:sensor,'LOW','OPEN','INFO')"), {"sensor": sensor})
try:
    command.upgrade(legacy_config, "b506173c2aac")
except Exception as exc:
    results["legacy_message_migration"] = type(exc).__name__ + ": " + str(exc).split("[SQL:")[0].strip()
# Simulate the missing message backfill solely to examine the next revision.
with legacy_engine.begin() as connection:
    connection.execute(text("ALTER TABLE alerts ADD COLUMN message VARCHAR(255) NOT NULL DEFAULT 'Legacy alert'"))
command.stamp(legacy_config, "b506173c2aac")
try:
    command.upgrade(legacy_config, "6808884c69fd")
except Exception as exc:
    results["legacy_enum_migration"] = type(exc).__name__ + ": " + str(exc).split("[SQL:")[0].strip()
settings.POSTGRES_DB = "audit"
legacy_engine.dispose()
engine.dispose()
print("AUDIT_RESULTS=" + json.dumps(results, ensure_ascii=False))
