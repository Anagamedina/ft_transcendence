from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.modules.alerts.model import Alert
from app.modules.alerts.repository import AlertRepository
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading  # noqa: F401 - registra el modelo ORM
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User  # noqa: F401 - registra el modelo ORM


@pytest.fixture()
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture()
def fixtures(db: Session):
    organization_a = Organization(name="A")
    organization_b = Organization(name="B")
    db.add_all([organization_a, organization_b])
    db.flush()

    site_a = Site(organization_id=organization_a.id, name="Site A")
    site_b = Site(organization_id=organization_b.id, name="Site B")
    db.add_all([site_a, site_b])
    db.flush()

    sensor_a = Sensor(
        site_id=site_a.id, external_id="sensor-a", name="Sensor A", unit="bar"
    )
    sensor_b = Sensor(
        site_id=site_b.id, external_id="sensor-b", name="Sensor B", unit="bar"
    )
    db.add_all([sensor_a, sensor_b])
    db.flush()
    return organization_a, organization_b, sensor_a, sensor_b


def test_create_persists_alert_as_active(db: Session, fixtures):
    _, _, sensor_a, _ = fixtures
    repository = AlertRepository(db)

    alert = repository.create(
        sensor_a.id, "HIGH_PRESSURE", "CRITICAL", "Presión por encima del umbral"
    )
    db.commit()

    assert alert.id is not None
    assert alert.status == "ACTIVE"
    assert alert.message == "Presión por encima del umbral"


def test_get_by_id_is_scoped_to_organization(db: Session, fixtures):
    organization_a, organization_b, sensor_a, _ = fixtures
    repository = AlertRepository(db)
    alert = repository.create(sensor_a.id, "LOW_PRESSURE", "WARNING", "Presión baja")
    db.commit()

    assert repository.get_by_id(alert.id, organization_a.id) is alert
    assert repository.get_by_id(alert.id, organization_b.id) is None


def test_list_by_organization_filters_by_status_and_sensor(db: Session, fixtures):
    organization_a, _, sensor_a, sensor_b_other_org = fixtures
    repository = AlertRepository(db)
    active = repository.create(sensor_a.id, "LOW_PRESSURE", "WARNING", "Baja")
    resolved = repository.create(sensor_a.id, "HIGH_PRESSURE", "CRITICAL", "Alta")
    resolved.status = "RESOLVED"
    db.commit()

    items, total = repository.list_by_organization(organization_a.id, status="ACTIVE")
    assert items == [active]
    assert total == 1

    items, total = repository.list_by_organization(
        organization_a.id, sensor_id=sensor_a.id
    )
    assert total == 2

    items, total = repository.list_by_organization(organization_a.id, status="RESOLVED")
    assert items == [resolved]


def test_acknowledge_sets_timestamp_once(db: Session, fixtures):
    _, _, sensor_a, _ = fixtures
    repository = AlertRepository(db)
    alert = repository.create(sensor_a.id, "LOW_PRESSURE", "WARNING", "Baja")
    db.commit()

    first = datetime(2026, 1, 1, tzinfo=timezone.utc)
    second = datetime(2026, 1, 2, tzinfo=timezone.utc)

    repository.acknowledge(alert.id, first)
    repository.acknowledge(alert.id, second)

    assert alert.acknowledged_at == first
    assert alert.status == "ACTIVE"


def test_resolve_sets_status_and_resolved_at(db: Session, fixtures):
    _, _, sensor_a, _ = fixtures
    repository = AlertRepository(db)
    alert = repository.create(sensor_a.id, "LOW_PRESSURE", "WARNING", "Baja")
    db.commit()

    when = datetime(2026, 1, 3, tzinfo=timezone.utc)
    repository.resolve(alert.id, when)

    assert alert.status == "RESOLVED"
    assert alert.resolved_at == when


def test_invalid_pagination_is_rejected(db: Session):
    repository = AlertRepository(db)

    with pytest.raises(ValueError):
        repository.list_by_organization(1, offset=-1)
    with pytest.raises(ValueError):
        repository.list_by_organization(1, limit=0)
