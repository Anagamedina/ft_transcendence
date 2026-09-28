"""
`POST /api/readings` de extremo a extremo (issue #24).

Los tests de `tests/unit/test_reading_service.py` prueban las reglas; estos
prueban el contrato HTTP: qué código y qué cuerpo sale por el endpoint, que
es lo que fijan los criterios de aceptación de la issue.

El más importante es `test_la_lectura_sobrevive_al_cierre_de_la_peticion`:
comprueba desde una sesión **distinta** que la fila sigue ahí. Sin él, un
201 devuelto sobre datos que nunca se confirmaron pasaría por bueno.
"""

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app
from app.modules.alerts.model import Alert  # noqa: F401 - registra el modelo ORM
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User  # noqa: F401 - registra el modelo ORM


@pytest.fixture()
def engine():
    # StaticPool mantiene UNA sola conexión: así la base en memoria es la
    # misma para la petición y para la sesión con la que comprobamos
    # después. Con el pool normal, cada conexión abriría una base vacía.
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture()
def sensor_id(engine):
    with Session(engine, expire_on_commit=False) as session:
        organization = Organization(name="Aguas del Norte")
        session.add(organization)
        session.flush()

        site = Site(organization_id=organization.id, name="Planta 1")
        session.add(site)
        session.flush()

        sensor = Sensor(
            site_id=site.id,
            external_id="sensor-01",
            name="Entrada principal",
            unit="bar",
        )
        session.add(sensor)
        session.commit()
        return sensor.id


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


def test_lectura_valida_devuelve_201(client, sensor_id):
    respuesta = client.post(
        "/api/readings",
        json={
            "sensor_id": str(sensor_id),
            "pressure": 3.42,
            "measured_at": "2026-09-24T09:15:00Z",
        },
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["sensor_id"] == str(sensor_id)
    assert cuerpo["pressure"] == pytest.approx(3.42)
    assert cuerpo["id"]
    assert cuerpo["created_at"]


def test_la_lectura_sobrevive_al_cierre_de_la_peticion(client, sensor_id, engine):
    """
    La comprobación que de verdad importa: se lee con OTRA sesión.

    Si el guardado se quedara en un `flush` sin confirmar, el endpoint
    seguiría devolviendo 201 con su id y aquí no habría ninguna fila.
    """
    client.post(
        "/api/readings",
        json={"sensor_id": str(sensor_id), "pressure": 3.42},
    )

    with Session(engine) as otra_sesion:
        guardada = otra_sesion.query(Reading).one()
        assert guardada.sensor_id == sensor_id
        assert float(guardada.value) == pytest.approx(3.42)
        assert guardada.unit == "bar"


def test_measured_at_es_opcional(client, sensor_id):
    respuesta = client.post(
        "/api/readings",
        json={"sensor_id": str(sensor_id), "pressure": 3.42},
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["measured_at"]


def test_sensor_desconocido_devuelve_404_con_su_codigo(client):
    respuesta = client.post(
        "/api/readings",
        json={"sensor_id": str(uuid4()), "pressure": 3.42},
    )

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "SENSOR_NOT_FOUND"


def test_presion_fuera_de_rango_es_422(client, sensor_id):
    """Fuera de 0-25 bar es un fallo de envío, no una anomalía que alertar."""
    respuesta = client.post(
        "/api/readings",
        json={"sensor_id": str(sensor_id), "pressure": 99.0},
    )

    assert respuesta.status_code == 422


def test_campo_desconocido_es_422(client, sensor_id):
    """
    `sensorId` en vez de `sensor_id` se rechaza entero en vez de ignorarse.
    Aceptarlo perdería la lectura en silencio.
    """
    respuesta = client.post(
        "/api/readings",
        json={"sensorId": str(sensor_id), "pressure": 3.42},
    )

    assert respuesta.status_code == 422


def test_una_lectura_rechazada_no_deja_rastro(client, engine):
    client.post(
        "/api/readings",
        json={"sensor_id": str(uuid4()), "pressure": 3.42},
    )

    with Session(engine) as otra_sesion:
        assert otra_sesion.query(Reading).count() == 0
