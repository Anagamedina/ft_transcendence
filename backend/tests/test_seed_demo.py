import hashlib
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401
from app.core.database import Base, get_db
from app.main import app
from app.modules.alerts.model import Alert
from app.modules.invitations.model import Invitation
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sensors.status import OFFLINE_TRAS
from app.modules.sites.model import Site
from app.modules.users.model import User
from seeds import seed_demo

DEMO_CREDENTIALS = {
    "admin@aquaguard.dev": "dev-admin-only",
    "client@aquaguard.dev": "dev-client-only",
}

# The ids that SIMULATOR_SENSOR_IDS and scripts/smoke.sh use.
SIMULATOR_AND_SMOKE_IDS = {
    "00000000-0000-4000-8000-000000000001",
    "00000000-0000-4000-8000-000000000002",
    "00000000-0000-4000-8000-000000000003",
}

ALL_MODELS = (Organization, User, Site, Sensor, Alert, Reading, Invitation)


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(autouse=True)
def _seed_against_test_engine(engine, monkeypatch):
    monkeypatch.setattr(
        seed_demo, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )


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


def _login(client, email):
    return client.post(
        "/api/auth/login", json={"email": email, "password": DEMO_CREDENTIALS[email]}
    )


def _now_naive():
    # SQLite gives datetimes back without time zone.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _naive(moment):
    return moment.replace(tzinfo=None) if moment.tzinfo else moment


def _counts(engine):
    with Session(engine) as session:
        return {model: session.query(model).count() for model in ALL_MODELS}


def _seed_like_the_old_version(engine):
    """What the previous seed left: one "Demo" organization and its sites."""
    with Session(engine) as session:
        organization = Organization(name=seed_demo.LEGACY_ORGANIZATION_NAME)
        session.add(organization)
        session.flush()
        session.add(
            User(
                organization_id=organization.id,
                email="admin@aquaguard.dev",
                name="Demo Admin",
                password_hash="seed-sha256$"
                + hashlib.sha256(b"dev-admin-only").hexdigest(),
                role="admin",
            )
        )
        site = Site(organization_id=organization.id, name="Hotel Mediterráneo")
        session.add(site)
        session.flush()
        session.add(
            Sensor(
                id=seed_demo._sensor_id(1),
                site_id=site.id,
                external_id="SENS-001",
                name="Presión entrada",
                low_threshold=Decimal("1.5"),
                high_threshold=Decimal("6"),
            )
        )
        session.commit()


# ---------------------------------------------------------
# Users
# ---------------------------------------------------------
@pytest.mark.parametrize("email", DEMO_CREDENTIALS)
def test_demo_users_can_log_in_after_seeding(client, email):
    seed_demo.seed()

    response = _login(client, email)

    assert response.status_code == 200
    assert response.json()["user"]["email"] == email


def test_demo_admin_is_global_and_client_belongs_to_an_organization(client):
    seed_demo.seed()

    admin = _login(client, "admin@aquaguard.dev").json()["user"]
    demo_client = _login(client, "client@aquaguard.dev").json()["user"]

    assert admin["organization_id"] is None
    assert demo_client["organization_id"] is not None


def test_seed_repairs_users_left_by_the_old_seed(client, engine):
    _seed_like_the_old_version(engine)
    assert _login(client, "admin@aquaguard.dev").status_code == 401

    seed_demo.seed()

    response = _login(client, "admin@aquaguard.dev")
    assert response.status_code == 200
    assert response.json()["user"]["organization_id"] is None


# ---------------------------------------------------------
# Organizations and sites
# ---------------------------------------------------------
def test_five_clients_in_different_states(engine):
    seed_demo.seed()

    with Session(engine) as session:
        organizations = {o.name: o for o in session.query(Organization)}

    assert set(organizations) == {
        "Residencias Alcalá",
        "Hotel Turia",
        "Comunidad Mallorca 401",
        "Polideportivo Abando",
        "Aguas del Sur",
    }
    assert {o.status for o in organizations.values()} == {"ACTIVE", "TRIAL", "SUSPENDED"}
    turia = organizations["Hotel Turia"]
    assert turia.status == "TRIAL"
    assert _naive(turia.trial_ends_at) > _now_naive()


def test_the_old_demo_organization_becomes_the_first_client(engine):
    _seed_like_the_old_version(engine)

    seed_demo.seed()

    with Session(engine) as session:
        names = {name for (name,) in session.query(Organization.name)}
        site_names = {name for (name,) in session.query(Site.name)}
    assert seed_demo.LEGACY_ORGANIZATION_NAME not in names
    assert len(names) == 5
    assert "Hotel Mediterráneo" not in site_names


def test_every_site_has_floors_and_real_coordinates(engine):
    seed_demo.seed()

    with Session(engine) as session:
        sites = session.query(Site).all()

    assert len(sites) == len(seed_demo.SITES)
    for site in sites:
        assert site.floors >= 1
        assert site.latitude is not None and site.longitude is not None
        assert site.building_type != "OTHER"
    assert any(site.basements > 0 for site in sites)


# ---------------------------------------------------------
# Sensors and readings
# ---------------------------------------------------------
def test_simulator_and_smoke_sensors_keep_their_ids(engine):
    seed_demo.seed()

    with Session(engine) as session:
        ids = {str(sensor_id) for (sensor_id,) in session.query(Sensor.id)}

    assert len(ids) == 8
    assert SIMULATOR_AND_SMOKE_IDS <= ids


def test_one_sensor_is_offline(engine):
    seed_demo.seed()
    offline_id = seed_demo._sensor_id(seed_demo.OFFLINE_SENSOR)

    with Session(engine) as session:
        last = (
            session.query(func.max(Reading.created_at))
            .filter(Reading.sensor_id == offline_id)
            .scalar()
        )

    assert _now_naive() - _naive(last) > OFFLINE_TRAS


def test_one_sensor_is_out_of_range(engine):
    seed_demo.seed()
    sensor_id = seed_demo._sensor_id(seed_demo.OUT_OF_RANGE_SENSOR)

    with Session(engine) as session:
        sensor = session.get(Sensor, sensor_id)
        last = (
            session.query(Reading)
            .filter(Reading.sensor_id == sensor_id)
            .order_by(Reading.recorded_at.desc())
            .first()
        )

    assert last.value > sensor.high_threshold


def test_there_are_readings_today(engine):
    seed_demo.seed()

    with Session(engine) as session:
        recent = (
            session.query(Reading)
            .filter(Reading.recorded_at >= _now_naive() - timedelta(hours=2))
            .count()
        )

    assert recent > 0


# ---------------------------------------------------------
# Alerts and invitation
# ---------------------------------------------------------
def test_alerts_of_the_last_30_days_with_who_handled_them(engine):
    seed_demo.seed()

    with Session(engine) as session:
        alerts = session.query(Alert).all()

    resolved = [a for a in alerts if a.status == "RESOLVED"]
    assert len(alerts) == 19
    assert len(resolved) == 16
    assert all(a.resolved_by is not None and a.acknowledged_by is not None for a in resolved)
    assert all(_now_naive() - _naive(a.created_at) < timedelta(days=30) for a in alerts)


def test_stray_active_alerts_are_resolved(engine):
    seed_demo.seed()
    with Session(engine) as session:
        session.add(
            Alert(
                sensor_id=seed_demo._sensor_id(1),
                alert_type="SENSOR_OFFLINE",
                status="ACTIVE",
                severity="CRITICAL",
                message="Abierta con el stack parado",
            )
        )
        session.commit()

    seed_demo.seed()

    with Session(engine) as session:
        active = session.query(Alert).filter(Alert.status == "ACTIVE").count()
    assert active == 3


def test_one_pending_invitation(engine):
    seed_demo.seed()

    with Session(engine) as session:
        invitation = session.query(Invitation).one()

    assert invitation.accepted_at is None
    assert invitation.revoked_at is None
    assert _naive(invitation.expires_at) > _now_naive()


# ---------------------------------------------------------
# Idempotency and production guard
# ---------------------------------------------------------
def test_seed_is_idempotent(engine):
    seed_demo.seed()
    before = _counts(engine)

    seed_demo.seed()

    assert _counts(engine) == before


def test_seed_refuses_to_run_in_production(engine, monkeypatch):
    monkeypatch.setattr(seed_demo.app_settings, "ENV", "production")

    with pytest.raises(SystemExit):
        seed_demo.seed()

    assert all(count == 0 for count in _counts(engine).values())
