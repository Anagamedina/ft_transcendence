"""
Tests del caso de uso `POST /api/readings` (issue #24).

Se prueban contra sqlite en memoria y los repositories reales, igual que
`test_sensor_reading_repositories.py`: lo que interesa aquí no es que el
service llame a un doble, sino que la traducción entre el contrato HTTP
(`pressure`, `measured_at`) y el esquema de la tabla (`value`, `unit`,
`recorded_at`) sea correcta de punta a punta.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.database import Base
from app.core.exceptions import NotFoundError
from app.modules.alerts.model import Alert
from app.modules.alerts.repository import AlertRepository
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
    return ReadingService(
        db, ReadingRepository(db), SensorRepository(db), AlertRepository(db)
    )


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


# ---------------------------------------------------------
# Reglas de presión al registrar una lectura (issue #28)
# ---------------------------------------------------------
# Umbrales del sensor de estos tests: mínimo 1.5 y máximo 10 bar. Con el
# margen crítico del 20 %, por debajo de 1.2 o por encima de 12 es CRITICAL.


@pytest.fixture()
def sensor_con_umbrales(db: Session, sensor):
    sensor.low_threshold = Decimal("1.500")
    sensor.high_threshold = Decimal("10.000")
    db.flush()
    return sensor


def _alertas(db: Session) -> list[Alert]:
    return db.query(Alert).order_by(Alert.created_at).all()


def test_una_lectura_normal_no_abre_alerta(service, sensor_con_umbrales, db: Session):
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=4.0))

    assert _alertas(db) == []


def test_una_lectura_baja_abre_low_pressure(service, sensor_con_umbrales, db: Session):
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=1.3))

    [alerta] = _alertas(db)
    assert alerta.alert_type == "LOW_PRESSURE"
    assert alerta.severity == "WARNING"
    assert alerta.status == "ACTIVE"
    assert alerta.message == "Presión por debajo del umbral: 1.3 bar (mínimo 1.5)"


def test_una_lectura_alta_abre_high_pressure(service, sensor_con_umbrales, db: Session):
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=12.5))

    [alerta] = _alertas(db)
    assert alerta.alert_type == "HIGH_PRESSURE"
    assert alerta.severity == "CRITICAL"


def test_justo_en_el_umbral_no_es_alerta(service, sensor_con_umbrales, db: Session):
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=1.5))
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=10.0))

    assert _alertas(db) == []


def test_sin_umbrales_no_hay_regla(service, sensor, db: Session):
    """Hasta la #97 la tabla admite sensores sin umbrales."""
    service.create(ReadingCreate(sensor_id=sensor.id, pressure=0.1))

    assert _alertas(db) == []


def test_varias_lecturas_bajas_son_una_sola_alerta(service, sensor_con_umbrales, db: Session):
    for presion in (1.4, 1.3, 1.45):
        service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=presion))

    assert len(_alertas(db)) == 1
    # Y las tres lecturas sí se guardan: la regla no se come ninguna.
    assert db.query(Reading).count() == 3


def test_baja_y_alta_son_alertas_distintas(service, sensor_con_umbrales, db: Session):
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=1.3))
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=11.0))

    assert {a.alert_type for a in _alertas(db)} == {"LOW_PRESSURE", "HIGH_PRESSURE"}


def test_si_empeora_la_alerta_sube_a_critical(service, sensor_con_umbrales, db: Session):
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=1.4))
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=0.9))

    [alerta] = _alertas(db)
    assert alerta.severity == "CRITICAL"
    # El mensaje cuenta la lectura que la ha empeorado, no la primera.
    assert alerta.message == "Presión por debajo del umbral: 0.9 bar (mínimo 1.5)"


def test_si_mejora_la_alerta_no_baja_a_warning(service, sensor_con_umbrales, db: Session):
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=0.9))
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=1.4))

    [alerta] = _alertas(db)
    assert alerta.severity == "CRITICAL"
    assert "0.9 bar" in alerta.message


def test_volver_al_rango_no_la_resuelve(service, sensor_con_umbrales, db: Session):
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=1.3))
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=4.0))

    [alerta] = _alertas(db)
    assert alerta.status == "ACTIVE"


def test_con_la_anterior_resuelta_se_abre_otra(service, sensor_con_umbrales, db: Session):
    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=1.3))
    [primera] = _alertas(db)
    primera.status = "RESOLVED"
    primera.resolved_at = datetime.now(timezone.utc)
    db.commit()

    service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=1.2))

    alertas = _alertas(db)
    assert len(alertas) == 2
    assert [a.status for a in alertas].count("ACTIVE") == 1


def test_si_falla_la_alerta_tampoco_se_guarda_la_lectura(
    service, sensor_con_umbrales, db: Session, monkeypatch
):
    """
    Lectura y alerta van en la misma transacción. Si la alerta no se puede
    guardar, no debe quedar una lectura fuera de rango sin su alerta.
    """
    db.commit()  # confirma el sensor, para que el rollback solo deshaga lo de create

    def _revienta(**_):
        raise RuntimeError("fallo al guardar la alerta")

    monkeypatch.setattr(service.alerts, "create", _revienta)

    with pytest.raises(RuntimeError):
        service.create(ReadingCreate(sensor_id=sensor_con_umbrales.id, pressure=1.3))

    assert db.query(Reading).count() == 0
    assert _alertas(db) == []
