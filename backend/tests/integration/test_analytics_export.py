"""
Analytics date range and CSV export (B18, issue #134).

Every test runs on SQLite and on a throwaway PostgreSQL database (`engine`
fixture in conftest.py): grouping by day uses date(), which behaves
differently in each.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.alerts.model import Alert
from app.modules.analytics.schemas import EXPORT_COLUMNS
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

# Fixed days at noon UTC, so no reading falls on a day boundary.
DAY_1 = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)
DAY_2 = datetime(2026, 9, 11, 12, 0, tzinfo=timezone.utc)
OLD = datetime(2026, 6, 1, 12, 0, tzinfo=timezone.utc)
PERIOD = {"from": "2026-09-10T00:00:00Z", "to": "2026-09-12T00:00:00Z"}


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
        name=f"Sensor {name}",
        low_threshold=Decimal("1.5"),
        high_threshold=Decimal("6"),
    )
    db.add(sensor)
    db.flush()
    return {"org": org, "client": client, "site": site, "sensor": sensor}


def _reading(sensor, value, moment):
    return Reading(sensor_id=sensor.id, value=Decimal(value), unit="bar", recorded_at=moment)


def _alert(sensor, moment, severity="WARNING", status="ACTIVE"):
    return Alert(
        sensor_id=sensor.id,
        alert_type="LOW_PRESSURE",
        status=status,
        severity=severity,
        message="Presión baja",
        created_at=moment,
    )


@pytest.fixture()
def data(engine):
    with Session(engine, expire_on_commit=False) as db:
        a = _organization(db, "A")
        b = _organization(db, "B")
        admin = User(
            organization_id=None,
            email="admin@test.test",
            name="Admin",
            password_hash="hashed",
            role="admin",
        )
        db.add(admin)
        sa, sb = a["sensor"], b["sensor"]
        db.add_all(
            [
                # A, day 1: three readings and two alerts (one CRITICAL resolved)
                _reading(sa, "2.000", DAY_1),
                _reading(sa, "3.000", DAY_1 + timedelta(hours=1)),
                _reading(sa, "4.000", DAY_1 + timedelta(hours=2)),
                _alert(sa, DAY_1, severity="CRITICAL", status="RESOLVED"),
                _alert(sa, DAY_1 + timedelta(hours=3)),
                # A, day 2: an alert without readings
                _alert(sa, DAY_2),
                # A, outside the period
                _reading(sa, "9.000", OLD),
                _alert(sa, OLD),
                # B, day 1
                _reading(sb, "5.000", DAY_1),
            ]
        )
        db.commit()
        return {"a": a, "b": b, "admin": admin}


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


def _export(client, **params):
    return client.get("/api/analytics/export", params={"format": "csv", **params})


def _rows(response) -> list[dict]:
    text = response.content.decode("utf-8-sig")  # strips the BOM
    return list(csv.DictReader(io.StringIO(text)))


# ---------------------------------------------------------
# Download
# ---------------------------------------------------------
def test_export_downloads_a_csv_with_the_documented_columns(client, data):
    _login(client, data["admin"])

    response = _export(client, **PERIOD)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert response.headers["content-disposition"] == (
        'attachment; filename="aquaguard-analytics_2026-09-10_2026-09-12.csv"'
    )
    assert response.content.startswith("﻿".encode())
    header = next(csv.reader(io.StringIO(response.content.decode("utf-8-sig"))))
    assert header == EXPORT_COLUMNS


def test_readings_and_alerts_are_aggregated_per_sensor_and_day(client, data):
    _login(client, data["a"]["client"])

    rows = _rows(_export(client, **PERIOD))

    assert [(r["date"], r["sensor_external_id"]) for r in rows] == [
        ("2026-09-10", "S-A"),
        ("2026-09-11", "S-A"),
    ]
    day_1, day_2 = rows
    assert day_1["organization"] == "A"
    assert day_1["site"] == "Edificio A"
    assert day_1["readings_count"] == "3"
    assert (day_1["pressure_min"], day_1["pressure_avg"], day_1["pressure_max"]) == (
        "2.000",
        "3.000",
        "4.000",
    )
    assert (day_1["alerts_total"], day_1["alerts_critical"], day_1["alerts_resolved"]) == (
        "2",
        "1",
        "1",
    )
    # A day with alerts and no readings still appears, pressure empty.
    assert day_2["readings_count"] == "0"
    assert day_2["pressure_avg"] == ""
    assert day_2["alerts_total"] == "1"


def test_nothing_outside_the_period_is_exported(client, data):
    _login(client, data["admin"])

    rows = _rows(_export(client, **PERIOD))

    assert all(r["pressure_max"] != "9.000" for r in rows)
    assert {r["date"] for r in rows} == {"2026-09-10", "2026-09-11"}


def test_default_period_is_the_last_30_days(client, engine, data):
    now = datetime.now(timezone.utc)
    with Session(engine) as db:
        db.add(_reading(data["a"]["sensor"], "3.300", now))
        db.add(_reading(data["a"]["sensor"], "7.700", now - timedelta(days=31)))
        db.commit()
    _login(client, data["a"]["client"])

    rows = _rows(_export(client))

    oldest_allowed = (now - timedelta(days=30)).date().isoformat()
    assert all(r["date"] >= oldest_allowed for r in rows)
    assert now.date().isoformat() in {r["date"] for r in rows}
    assert "7.700" not in {r["pressure_max"] for r in rows}


def test_a_date_without_time_zone_is_utc(client, data):
    _login(client, data["admin"])

    rows = _rows(_export(client, **{"from": "2026-09-10", "to": "2026-09-11"}))

    assert {r["date"] for r in rows} == {"2026-09-10"}


# ---------------------------------------------------------
# Organization scope
# ---------------------------------------------------------
def test_a_client_only_exports_its_organization(client, data):
    _login(client, data["b"]["client"])

    rows = _rows(_export(client, **PERIOD))

    assert {r["organization"] for r in rows} == {"B"}


def test_an_admin_exports_every_organization(client, data):
    _login(client, data["admin"])

    rows = _rows(_export(client, **PERIOD))

    assert {r["organization"] for r in rows} == {"A", "B"}


def test_without_session_it_is_401(client, data):
    assert _export(client, **PERIOD).status_code == 401


# ---------------------------------------------------------
# Invalid input → 422
# ---------------------------------------------------------
@pytest.mark.parametrize(
    "params",
    [
        {"from": "2026-09-12", "to": "2026-09-10"},  # from after to
        {"from": "2026-09-10", "to": "2026-09-10"},  # empty period
        {"from": "2025-01-01", "to": "2026-09-10"},  # longer than 366 days
    ],
)
def test_an_invalid_period_is_422(client, data, params):
    _login(client, data["admin"])

    response = _export(client, **params)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "INVALID_DATE_RANGE"


@pytest.mark.parametrize(
    "params",
    [
        {"from": "ayer"},
        {"to": "2026-13-45"},
        {"format": "pdf"},
    ],
)
def test_malformed_input_is_422(client, data, params):
    _login(client, data["admin"])

    response = _export(client, **params)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# ---------------------------------------------------------
# format=json (used by the analytics panel, F19)
# ---------------------------------------------------------
def test_json_returns_the_same_rows_with_real_types(client, data):
    _login(client, data["a"]["client"])

    response = _export(client, format="json", **PERIOD)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert "content-disposition" not in response.headers
    rows = response.json()
    assert [r["date"] for r in rows] == ["2026-09-10", "2026-09-11"]
    assert set(rows[0]) == set(EXPORT_COLUMNS)
    assert rows[0]["readings_count"] == 3
    assert rows[0]["pressure_avg"] == 3.0
    assert rows[0]["alerts_critical"] == 1
    # No readings that day: null, not an empty string.
    assert rows[1]["pressure_avg"] is None


def test_json_respects_the_organization(client, data):
    _login(client, data["b"]["client"])

    rows = _export(client, format="json", **PERIOD).json()

    assert {r["organization"] for r in rows} == {"B"}


# ---------------------------------------------------------
# B9 dashboard KPIs and alert aggregations
# ---------------------------------------------------------
def test_overview_is_scoped_and_returns_kpis(client, engine, data):
    now = datetime.now(timezone.utc)
    with Session(engine) as db:
        db.add(
            Alert(
                sensor_id=data["a"]["sensor"].id,
                alert_type="LOW_PRESSURE",
                status="RESOLVED",
                severity="WARNING",
                message="Resuelta",
                created_at=now - timedelta(minutes=30),
                resolved_at=now,
            )
        )
        db.commit()

    _login(client, data["admin"])
    response = client.get("/api/analytics/overview")

    assert response.status_code == 200
    body = response.json()
    assert body["organizations_total"] == 2
    assert body["organizations_needing_attention"] == 1
    assert body["sites_total"] == 2
    assert body["sensors_total"] == 2
    assert body["open_alerts"] == 2
    assert body["critical_open_alerts"] == 0
    assert body["median_resolution_minutes"] == pytest.approx(30, abs=0.1)

    _login(client, data["a"]["client"])
    client_body = client.get("/api/analytics/overview").json()
    assert client_body["organizations_total"] is None
    assert client_body["sites_total"] == 1
    assert client_body["open_alerts"] == 2


def test_weekly_alerts_returns_seven_days_and_zero_sensor_rows(client, data):
    _login(client, data["a"]["client"])

    response = client.get(
        "/api/analytics/alerts/weekly",
        params={"site_id": str(data["a"]["site"].id), "week_start": "2026-09-07"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["week_start"] == "2026-09-07"
    assert len(body["days"]) == 7
    assert len(body["rows"]) == 1
    assert sum(body["rows"][0]["counts"]) == 3


def test_weekly_rejects_non_monday_and_hides_other_organization(client, data):
    _login(client, data["a"]["client"])
    invalid = client.get(
        "/api/analytics/alerts/weekly",
        params={"site_id": str(data["a"]["site"].id), "week_start": "2026-09-10"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "INVALID_WEEK_START"

    hidden = client.get(
        "/api/analytics/alerts/weekly",
        params={"site_id": str(data["b"]["site"].id), "week_start": "2026-09-07"},
    )
    assert hidden.status_code == 404
    assert hidden.json()["error"]["code"] == "SITE_NOT_FOUND"


def test_top_sensors_returns_scoped_ranked_items(client, data):
    _login(client, data["admin"])

    response = client.get("/api/analytics/alerts/top-sensors", params={"days": 60})

    assert response.status_code == 200
    body = response.json()
    assert body["days"] == 60
    assert body["items"][0]["sensor_id"] == str(data["a"]["sensor"].id)
    assert body["items"][0]["alert_count"] >= 4
    assert body["items"][0]["critical_count"] == 1

    _login(client, data["b"]["client"])
    client_items = client.get("/api/analytics/alerts/top-sensors", params={"days": 60}).json()["items"]
    assert all(item["organization_name"] == "B" for item in client_items)
