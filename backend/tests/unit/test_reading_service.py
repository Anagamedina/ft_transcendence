"""
Tests del caso de uso `POST /api/readings` (issue #24).

Se prueban contra sqlite en memoria y los repositories reales, igual que
`test_sensor_reading_repositories.py`: lo que interesa aquí no es que el
service llame a un doble, sino que la traducción entre el contrato HTTP
(`pressure`, `measured_at`) y el esquema de la tabla (`value`, `unit`,
`recorded_at`) sea correcta de punta a punta.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.exceptions import NotFoundError
from app.modules.alerts.model import Alert  # noqa: F401 - registra el modelo ORM
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.readings.repository import ReadingRepository
from app.modules.readings.schemas import ReadingCreate
from app.modules.readings.service import ReadingService
from app.modules.sensors.model import Sensor
from app.modules.sensors.repository import SensorRepository
from app.modules.sites.model import Site
from app.modules.users.model import User  # noqa: F401 - registra el modelo ORM


@pytest.fixture()
def db():
    """
    Sesión de pruebas con la MISMA configuración que la de la aplicación.

    `expire_on_commit=False` no es un adorno copiado: es lo que usa
    `SessionLocal` en `core/database.py`. Con el valor por defecto
    (`True`), al confirmar se vacían los atributos y se releen de la base
    — y sqlite devuelve las fechas sin zona horaria, cosa que PostgreSQL
    (`timestamptz`) no hace. El test fallaría por una diferencia del motor
    de pruebas, no por un fallo del código.
    """
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine, expire_on_commit=False) as session:
        yield session


@pytest.fixture()
def sensor(db: Session):
    organization = Organization(name="Aguas del Norte")
    db.add(organization)
    db.flush()

    site = Site(organization_id=organization.id, name="Planta 1")
    db.add(site)
    db.flush()

    sensor = Sensor(
        site_id=site.id,
        external_id="sensor-01",
        name="Entrada principal",
        unit="bar",
    )
    db.add(sensor)
    db.flush()
    return sensor


@pytest.fixture()
def service(db: Session):
    return ReadingService(db, ReadingRepository(db), SensorRepository(db))


def test_guarda_la_lectura_y_la_devuelve(service, sensor, db: Session):
    medida = datetime(2026, 9, 24, 9, 15, tzinfo=timezone.utc)

    resultado = service.create(
        ReadingCreate(sensor_id=sensor.id, pressure=3.42, measured_at=medida)
    )

    assert resultado.sensor_id == sensor.id
    assert resultado.pressure == pytest.approx(3.42)
    assert resultado.id is not None

    # Y de verdad está en la tabla, no solo en la respuesta.
    guardada = db.query(Reading).one()
    assert guardada.sensor_id == sensor.id
    assert float(guardada.value) == pytest.approx(3.42)


def test_traduce_los_nombres_del_contrato_al_de_la_tabla(service, sensor, db: Session):
    """`pressure` acaba en `value`, y `measured_at` en `recorded_at`."""
    medida = datetime(2026, 9, 24, 9, 15, tzinfo=timezone.utc)

    service.create(
        ReadingCreate(sensor_id=sensor.id, pressure=7.5, measured_at=medida)
    )

    guardada = db.query(Reading).one()
    assert float(guardada.value) == pytest.approx(7.5)
    assert guardada.recorded_at.replace(tzinfo=timezone.utc) == medida


def test_la_unidad_se_copia_del_sensor(service, sensor, db: Session):
    """
    No es una constante "bar": si el sensor declara otra unidad, la
    lectura hereda esa. Así la lectura no puede contradecir al aparato.
    """
    sensor.unit = "psi"
    db.flush()

    service.create(ReadingCreate(sensor_id=sensor.id, pressure=2.0))

    assert db.query(Reading).one().unit == "psi"


def test_sensor_inexistente_da_404_con_codigo_propio(service):
    inventado = "6f1c8a2e-6b3d-4f9a-9c21-0b7e5d3a9d4b"

    with pytest.raises(NotFoundError) as error:
        service.create(ReadingCreate(sensor_id=inventado, pressure=3.0))

    # El código específico es parte del contrato: el interceptor de Axios
    # del frontend ramifica por él, no por el mensaje.
    assert error.value.code == "SENSOR_NOT_FOUND"


def test_sin_sensor_no_se_guarda_nada(service, db: Session):
    """Una `sensor_id` inventada no debe dejar lecturas huérfanas."""
    inventado = "6f1c8a2e-6b3d-4f9a-9c21-0b7e5d3a9d4b"

    with pytest.raises(NotFoundError):
        service.create(ReadingCreate(sensor_id=inventado, pressure=3.0))

    assert db.query(Reading).count() == 0


def test_sin_measured_at_usa_el_momento_de_recepcion(service, sensor, db: Session):
    antes = datetime.now(timezone.utc)

    resultado = service.create(ReadingCreate(sensor_id=sensor.id, pressure=3.0))

    despues = datetime.now(timezone.utc)
    assert antes - timedelta(seconds=1) <= resultado.measured_at <= despues + timedelta(seconds=1)


def test_measured_at_sin_zona_horaria_se_asume_utc(service, sensor, db: Session):
    """
    Guardar un datetime *naive* junto a otros con zona hace que las
    comparaciones fallen, y en un histórico eso son lecturas ordenadas al
    azar.
    """
    naive = datetime(2026, 9, 24, 9, 15)

    resultado = service.create(
        ReadingCreate(sensor_id=sensor.id, pressure=3.0, measured_at=naive)
    )

    assert resultado.measured_at.tzinfo is not None
    assert resultado.measured_at == naive.replace(tzinfo=timezone.utc)
