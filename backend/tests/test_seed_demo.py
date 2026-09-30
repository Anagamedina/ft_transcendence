import hashlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401
from app.core.database import Base, get_db
from app.main import app
from app.modules.organizations.model import Organization
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User
from seeds import seed_demo

DEMO_CREDENTIALS = {
    "admin@aquaguard.dev": "dev-admin-only",
    "client@aquaguard.dev": "dev-client-only",
}


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


def _seed_like_the_old_version(engine):
    with Session(engine) as session:
        organization = Organization(name=seed_demo.ORGANIZATION_NAME)
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
        session.commit()


@pytest.mark.parametrize("email", DEMO_CREDENTIALS)
def test_demo_users_can_log_in_after_seeding(client, email):
    seed_demo.seed()

    response = _login(client, email)

    assert response.status_code == 200
    assert response.json()["user"]["email"] == email


def test_demo_admin_is_global_and_client_belongs_to_demo_organization(client):
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


def test_demo_sensors_have_the_ids_the_simulator_expects(engine):
    seed_demo.seed()

    with Session(engine) as session:
        ids = {str(sensor_id) for (sensor_id,) in session.query(Sensor.id)}

    assert ids == {
        "00000000-0000-4000-8000-000000000001",
        "00000000-0000-4000-8000-000000000002",
        "00000000-0000-4000-8000-000000000003",
    }


def test_seed_is_idempotent(engine):
    seed_demo.seed()
    with Session(engine) as session:
        before = {
            model: session.query(model).count()
            for model in (Organization, User, Site, Sensor)
        }

    seed_demo.seed()

    with Session(engine) as session:
        after = {
            model: session.query(model).count()
            for model in (Organization, User, Site, Sensor)
        }
    assert after == before
