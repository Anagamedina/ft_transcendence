"""
Restricciones de la tabla `sensors` (issue #97).

El schema ya valida estos casos, pero la base tiene que rechazarlos
también si alguien entra por otro camino (seed, SQL a mano).
"""

from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import Base
from app.modules.alerts.model import Alert  # noqa: F401 - registra el modelo ORM
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
def site(db: Session):
    organization = Organization(name="A")
    db.add(organization)
    db.flush()
    site = Site(organization_id=organization.id, name="Site A")
    db.add(site)
    db.flush()
    return site


def _sensor(site: Site, **overrides) -> Sensor:
    campos = {
        "site_id": site.id,
        "external_id": "sensor-01",
        "name": "Entrada principal",
        "unit": "bar",
        "low_threshold": Decimal("1.500"),
        "high_threshold": Decimal("6.000"),
    }
    campos.update(overrides)
    return Sensor(**campos)


def test_sensor_valido_toma_pressure_por_defecto(db: Session, site):
    sensor = _sensor(site, location="Sala técnica")
    db.add(sensor)
    db.flush()
    db.refresh(sensor)

    assert sensor.sensor_type == "PRESSURE"
    assert sensor.location == "Sala técnica"


@pytest.mark.parametrize("campo", ["low_threshold", "high_threshold"])
def test_umbral_nulo_se_rechaza(db: Session, site, campo):
    db.add(_sensor(site, **{campo: None}))

    with pytest.raises(IntegrityError):
        db.flush()


@pytest.mark.parametrize(
    ("bajo", "alto"),
    [(Decimal("6.000"), Decimal("1.500")), (Decimal("3.000"), Decimal("3.000"))],
)
def test_umbral_inferior_debe_ser_menor_que_superior(db: Session, site, bajo, alto):
    db.add(_sensor(site, low_threshold=bajo, high_threshold=alto))

    with pytest.raises(IntegrityError):
        db.flush()


@pytest.mark.parametrize(
    ("bajo", "alto"),
    [(Decimal("-0.500"), Decimal("6.000")), (Decimal("1.500"), Decimal("25.500"))],
)
def test_umbral_fuera_de_rango_se_rechaza(db: Session, site, bajo, alto):
    db.add(_sensor(site, low_threshold=bajo, high_threshold=alto))

    with pytest.raises(IntegrityError):
        db.flush()


def test_umbrales_en_los_extremos_del_rango_se_aceptan(db: Session, site):
    db.add(_sensor(site, low_threshold=Decimal("0"), high_threshold=Decimal("25")))
    db.flush()


def test_unit_toma_bar_por_defecto(db: Session, site):
    sensor = Sensor(
        site_id=site.id,
        external_id="sensor-01",
        name="Entrada principal",
        low_threshold=Decimal("1.500"),
        high_threshold=Decimal("6.000"),
    )
    db.add(sensor)
    db.flush()
    db.refresh(sensor)

    assert sensor.unit == "bar"


def test_sensor_type_desconocido_se_rechaza(db: Session, site):
    db.add(_sensor(site, sensor_type="TEMPERATURE"))

    with pytest.raises(IntegrityError):
        db.flush()
