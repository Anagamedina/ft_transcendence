"""
Columns and constraints added for the main screens (D1 + D2, issue #129).

Runs on SQLite, which also enforces CHECK constraints. The PostgreSQL side
(migrations 0a42a9879db8 and 8e879672702c) is covered by `make migration-check`.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import models  # noqa: F401 - registers the ORM models
from app.core.database import Base
from app.modules.organizations.model import Organization
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def org(db: Session) -> Organization:
    org = Organization(name="Org A")
    db.add(org)
    db.flush()
    return org


def _user(org_id, role, email="u@example.com"):
    return User(
        organization_id=org_id,
        email=email,
        name="U",
        password_hash="hashed",
        role=role,
    )


def test_defaults_for_new_rows(db: Session, org: Organization):
    site = Site(organization_id=org.id, name="Edificio")
    db.add(site)
    db.flush()
    sensor = Sensor(
        site_id=site.id,
        external_id="S-1",
        name="Sensor",
        low_threshold=1,
        high_threshold=5,
    )
    user = _user(org.id, "client")
    db.add_all([sensor, user])
    db.flush()
    for row in (org, site, sensor, user):
        db.refresh(row)

    assert org.status == "ACTIVE"
    assert org.trial_ends_at is None
    assert (site.floors, site.basements, site.building_type) == (1, 0, "OTHER")
    assert sensor.floor == 0
    assert user.is_active is True
    assert user.last_login_at is None


def test_organization_status_outside_enum_is_rejected(db: Session):
    db.add(Organization(name="Org B", status="DELETED"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_building_type_outside_enum_is_rejected(db: Session, org: Organization):
    db.add(Site(organization_id=org.id, name="Castillo", building_type="CASTLE"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_site_needs_at_least_one_floor(db: Session, org: Organization):
    db.add(Site(organization_id=org.id, name="Solar", floors=0))
    with pytest.raises(IntegrityError):
        db.flush()


def test_client_without_organization_is_rejected(db: Session):
    db.add(_user(None, "client"))
    with pytest.raises(IntegrityError):
        db.flush()


def test_admin_without_organization_is_allowed(db: Session):
    db.add(_user(None, "admin"))
    db.flush()
