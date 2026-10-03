"""
Clave del simulador en `POST /api/readings` (issue #106).

`POST /api/readings` no pide sesión, porque quien manda lecturas es el
simulador y no una persona. Lo único que lo protege es la cabecera
`X-Ingest-Key`, que tiene que coincidir con `INGEST_API_KEY` del .env.
Sin ella, cualquiera podría mandar lecturas y abrir alertas falsas (#28).
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.app_config import app_settings
from app.core.database import Base, get_db
from app.main import app
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site

BACKEND = Path(__file__).resolve().parents[1]


@pytest.fixture()
def engine():
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
        org = Organization(name="Aguas del Norte")
        session.add(org)
        session.flush()
        site = Site(organization_id=org.id, name="Planta 1")
        session.add(site)
        session.flush()
        sensor = Sensor(site_id=site.id, external_id="sensor-01", name="Entrada", unit="bar")
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


def _lectura(client, sensor_id, cabeceras=None):
    return client.post(
        "/api/readings",
        json={"sensor_id": str(sensor_id), "pressure": 3.5},
        headers=cabeceras or {},
    )


def _lecturas_guardadas(engine):
    with Session(engine) as session:
        return session.query(Reading).count()


# ---------------------------------------------------------
# La cabecera
# ---------------------------------------------------------
def test_sin_clave_da_401_y_no_guarda_nada(client, sensor_id, engine):
    respuesta = _lectura(client, sensor_id)

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "UNAUTHORIZED"
    assert _lecturas_guardadas(engine) == 0


def test_con_una_clave_equivocada_da_401_y_no_guarda_nada(client, sensor_id, engine):
    respuesta = _lectura(client, sensor_id, {"X-Ingest-Key": "no-es-la-clave"})

    assert respuesta.status_code == 401
    assert _lecturas_guardadas(engine) == 0


def test_sin_clave_y_con_clave_mala_responden_lo_mismo(client, sensor_id):
    """Decir cuál de los dos casos es da pistas a quien está probando."""
    sin = _lectura(client, sensor_id).json()
    mala = _lectura(client, sensor_id, {"X-Ingest-Key": "no-es-la-clave"}).json()

    assert sin == mala


def test_con_la_clave_buena_guarda_la_lectura(client, sensor_id, engine):
    respuesta = _lectura(
        client, sensor_id, {"X-Ingest-Key": app_settings.INGEST_API_KEY}
    )

    assert respuesta.status_code == 201
    assert _lecturas_guardadas(engine) == 1


def test_vale_la_clave_del_env_y_no_la_de_por_defecto(client, sensor_id, monkeypatch):
    """Cuando alguien define su propia INGEST_API_KEY, la de ejemplo deja de valer."""
    monkeypatch.setattr(app_settings, "INGEST_API_KEY", "la-clave-de-produccion")

    con_la_de_ejemplo = _lectura(client, sensor_id, {"X-Ingest-Key": "dev-only-ingest-key"})
    con_la_nueva = _lectura(client, sensor_id, {"X-Ingest-Key": "la-clave-de-produccion"})

    assert con_la_de_ejemplo.status_code == 401
    assert con_la_nueva.status_code == 201


def test_las_rutas_con_sesion_no_aceptan_la_clave_en_su_lugar(client):
    """La clave abre solo POST /api/readings, no sirve como sesión."""
    respuesta = client.get(
        "/api/alerts", headers={"X-Ingest-Key": app_settings.INGEST_API_KEY}
    )

    assert respuesta.status_code == 401


# ---------------------------------------------------------
# Producción
# ---------------------------------------------------------
def _arrancar_config(**entorno):
    """
    Carga app_config en un proceso aparte, con el entorno indicado.

    Va en otro proceso porque la comprobación se hace al importar el módulo,
    y aquí ya está importado.
    """
    env = {**os.environ, **entorno}
    return subprocess.run(
        [sys.executable, "-c", "import app.core.app_config"],
        cwd=BACKEND,
        env=env,
        capture_output=True,
        text=True,
    )


def test_en_produccion_no_arranca_con_la_clave_de_ejemplo():
    resultado = _arrancar_config(
        ENV="production",
        SECRET_KEY="una-clave-de-sesion-de-verdad",
        INGEST_API_KEY="dev-only-ingest-key",
    )

    assert resultado.returncode != 0
    assert "INGEST_API_KEY" in resultado.stderr


def test_en_produccion_arranca_con_una_clave_propia():
    resultado = _arrancar_config(
        ENV="production",
        SECRET_KEY="una-clave-de-sesion-de-verdad",
        INGEST_API_KEY="una-clave-del-simulador-de-verdad",
    )

    assert resultado.returncode == 0, resultado.stderr
