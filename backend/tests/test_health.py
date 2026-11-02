"""
Endpoints de salud (issue #30): `GET /api/health` y `GET /api/health/db`.

No los usa ninguna persona: los usan las máquinas. Docker llama a
`/api/health` para saber si el contenedor del backend sigue vivo, y
`make smoke` y el simulador llaman a `/api/health/db` para saber si el
backend ya puede trabajar con la base. Si alguien los cambia sin querer,
el fallo aparecería lejos de aquí y costaría encontrarlo.
"""

from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.app_config import APP_NAME, APP_VERSION
from app.core.database import get_db
from app.main import app

# Lo que contendría el error real de una base caída: la cadena de conexión,
# con usuario, contraseña y host. No debe llegar nunca a la respuesta.
_SECRETO = "postgresql://aquaguard:contrasena-secreta@database:5432/aquaguard"


@pytest.fixture()
def client():
    yield TestClient(app)
    app.dependency_overrides.clear()


def _con_base_que_funciona():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    def _get_db():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[get_db] = _get_db


class _SesionCaida:
    """Una sesión cuya base no responde, como cuando PostgreSQL está parado."""

    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception(f"could not connect to {_SECRETO}"))


def _con_base_caida():
    def _get_db():
        yield _SesionCaida()

    app.dependency_overrides[get_db] = _get_db


# ---------------------------------------------------------
# GET /api/health · ¿está vivo el proceso?
# ---------------------------------------------------------
def test_health_responde_ok(client):
    respuesta = client.get("/api/health")

    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION,
    }


def test_health_no_depende_de_la_base(client):
    """
    Con la base caída, `/api/health` tiene que seguir respondiendo. Si no,
    Docker reiniciaría el backend en bucle cada vez que cae PostgreSQL,
    sin arreglar nada.
    """
    _con_base_caida()

    assert client.get("/api/health").status_code == 200


# ---------------------------------------------------------
# GET /api/health/db · ¿puede trabajar con la base?
# ---------------------------------------------------------
def test_health_db_con_la_base_funcionando(client):
    _con_base_que_funciona()

    respuesta = client.get("/api/health/db")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["status"] == "ok"
    assert cuerpo["database"] == "connected"
    # Es una fecha de verdad, no un texto cualquiera.
    datetime.fromisoformat(cuerpo["checked_at"].replace("Z", "+00:00"))


def test_health_db_con_la_base_caida_da_503(client):
    _con_base_caida()

    respuesta = client.get("/api/health/db")

    assert respuesta.status_code == 503
    assert respuesta.json()["error"]["code"] == "DATABASE_UNAVAILABLE"


def test_el_error_no_ensena_la_conexion_a_la_base(client):
    """
    El error real de SQLAlchemy incluye la cadena de conexión. Devolverlo
    tal cual le daría a cualquiera el usuario, la contraseña y el host de
    PostgreSQL.
    """
    _con_base_caida()

    texto = client.get("/api/health/db").text

    assert "contrasena-secreta" not in texto
    assert "postgresql://" not in texto
    assert "database:5432" not in texto
