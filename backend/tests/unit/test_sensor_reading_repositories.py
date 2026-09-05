from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.modules.alerts.model import Alert  # noqa: F401 - registra el modelo ORM
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.readings.repository import ReadingRepository
from app.modules.sensors.model import Sensor
from app.modules.sensors.repository import SensorRepository
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
        site_id=site_a.id,
        external_id="sensor-a",
        name="Sensor A",
        unit="bar",
    )
    sensor_b = Sensor(
        site_id=site_b.id,
        external_id="sensor-b",
        name="Sensor B",
        unit="bar",
    )
    db.add_all([sensor_a, sensor_b])
    db.flush()
    return organization_a, organization_b, sensor_a, sensor_b


def test_sensor_queries_are_scoped_to_organization(db: Session, fixtures):
    organization_a, organization_b, sensor_a, sensor_b = fixtures
    repository = SensorRepository(db)

    items, total = repository.list_by_organization(organization_a.id)

    assert [sensor.id for sensor in items] == [sensor_a.id]
    assert total == 1
    assert repository.get_by_id(sensor_a.id, organization_a.id) is sensor_a
    assert repository.get_by_id(sensor_b.id, organization_a.id) is None
    assert repository.get_by_id(sensor_a.id, organization_b.id) is None


def test_reading_create_flushes_and_history_is_stable_and_paginated(
    db: Session, fixtures
):
    organization_a, _, sensor_a, _ = fixtures
    repository = ReadingRepository(db)
    timestamp = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

    first = repository.create(sensor_a.id, 2.5, "bar", timestamp)
    second = repository.create(sensor_a.id, 3.5, "bar", timestamp)
    db.commit()

    items, total = repository.list_by_sensor(
        sensor_a.id, organization_a.id, offset=0, limit=1
    )

    assert first.id is not None
    assert total == 2
    assert items == [first]

    items, _ = repository.list_by_sensor(
        sensor_a.id, organization_a.id, offset=1, limit=1
    )
    assert items == [second]


def test_history_does_not_cross_organization_boundary(db: Session, fixtures):
    organization_a, organization_b, sensor_a, sensor_b = fixtures
    repository = ReadingRepository(db)
    repository.create(
        sensor_b.id,
        4.0,
        "bar",
        datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    db.commit()

    items, total = repository.list_by_sensor(
        sensor_b.id, organization_a.id
    )
    assert items == []
    assert total == 0

    items, total = repository.list_by_sensor(
        sensor_b.id, organization_b.id
    )
    assert len(items) == 1
    assert total == 1


def test_invalid_pagination_is_rejected(db: Session):
    repository = SensorRepository(db)

    with pytest.raises(ValueError):
        repository.list_by_organization(1, offset=-1)
    with pytest.raises(ValueError):
        repository.list_by_organization(1, limit=0)

    readings = ReadingRepository(db)
    with pytest.raises(ValueError):
        readings.list_by_sensor(1, 1, offset=-1)
    with pytest.raises(ValueError):
        readings.list_by_sensor(1, 1, limit=0)
