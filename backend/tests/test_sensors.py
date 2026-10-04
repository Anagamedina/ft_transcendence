"""
Sensores (issue #25): `GET /api/sensors` y `GET /api/sensors/{id}`.

Mismo alcance que el resto de la API desde la #27: un admin ve los sensores
de todas las organizaciones; un cliente, solo los suyos. Que sin sesión
respondan 401 ya lo comprueba `test_permisos.py`.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

AHORA = datetime.now(timezone.utc)


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def _sensor(session, site, nombre, **extra):
    sensor = Sensor(
        site_id=site.id,
        external_id=f"SENS-{nombre}",
        name=nombre,
        unit="bar",
        low_threshold=Decimal("1.500"),
        high_threshold=Decimal("6.000"),
        **extra,
    )
    session.add(sensor)
    session.flush()
    return sensor


def _lectura(session, sensor, recibida):
    session.add(
        Reading(
            sensor_id=sensor.id,
            value=Decimal("3.5"),
            unit="bar",
            recorded_at=recibida,
            created_at=recibida,
        )
    )


def _usuario(session, email, role, organization_id):
    user = User(
        organization_id=organization_id,
        email=email,
        name=email.split("@")[0],
        password_hash="da-igual-aqui",
        role=role,
    )
    session.add(user)
    return user


@pytest.fixture()
def datos(engine):
    with Session(engine, expire_on_commit=False) as session:
        a = Organization(name="Cliente A")
        b = Organization(name="Cliente B")
        session.add_all([a, b])
        session.flush()
        site_a = Site(organization_id=a.id, name="Hotel")
        site_b = Site(organization_id=b.id, name="Depósito")
        session.add_all([site_a, site_b])
        session.flush()

        # Nombres elegidos para comprobar el orden: Caldera < Entrada < Salida.
        entrada = _sensor(session, site_a, "Entrada", location="Sala técnica")
        caldera = _sensor(session, site_a, "Caldera", sensor_type="FLOW")
        salida = _sensor(session, site_b, "Salida")

        _lectura(session, entrada, AHORA - timedelta(seconds=10))  # reciente
        _lectura(session, entrada, AHORA - timedelta(hours=2))  # antigua, no cuenta
        _lectura(session, salida, AHORA - timedelta(hours=1))  # solo antiguas
        # caldera: ninguna lectura

        usuarios = {
            "admin": _usuario(session, "admin@aquaguard.dev", "admin", None),
            "cliente_a": _usuario(session, "a@aquaguard.dev", "client", a.id),
        }
        session.commit()
        return {"entrada": entrada, "caldera": caldera, "salida": salida, **usuarios}


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


def _entrar(client, user):
    client.cookies.set(SESSION_COOKIE, create_session_token(user.id))


def _por_nombre(respuesta):
    return {s["name"]: s for s in respuesta.json()["items"]}


# ---------------------------------------------------------
# GET /api/sensors
# ---------------------------------------------------------
def test_el_admin_ve_los_sensores_de_todas_las_organizaciones(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.get("/api/sensors")

    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 3
    assert [s["name"] for s in respuesta.json()["items"]] == ["Caldera", "Entrada", "Salida"]


def test_un_cliente_solo_ve_los_suyos(client, datos):
    _entrar(client, datos["cliente_a"])

    respuesta = client.get("/api/sensors")

    assert respuesta.json()["total"] == 2
    assert set(_por_nombre(respuesta)) == {"Caldera", "Entrada"}


def test_el_estado_sale_de_la_ultima_lectura(client, datos):
    """
    Entrada tiene una lectura de hace 10 s → ONLINE.
    Salida solo tiene una de hace 1 h → OFFLINE.
    Caldera no tiene ninguna → OFFLINE y sin `last_seen_at`.
    """
    _entrar(client, datos["admin"])

    sensores = _por_nombre(client.get("/api/sensors"))

    assert sensores["Entrada"]["status"] == "ONLINE"
    assert sensores["Salida"]["status"] == "OFFLINE"
    assert sensores["Caldera"]["status"] == "OFFLINE"
    assert sensores["Caldera"]["last_seen_at"] is None


def test_last_seen_at_es_la_lectura_mas_reciente(client, datos):
    """Entrada tiene dos lecturas; cuenta la de hace 10 s, no la de hace 2 h."""
    _entrar(client, datos["admin"])

    entrada = _por_nombre(client.get("/api/sensors"))["Entrada"]
    vista = datetime.fromisoformat(entrada["last_seen_at"].replace("Z", "+00:00"))

    assert abs(vista - (AHORA - timedelta(seconds=10))) < timedelta(seconds=1)


def test_los_campos_del_contrato_salen_bien(client, datos):
    """La tabla dice low/high_threshold; el contrato, min/max_pressure."""
    _entrar(client, datos["admin"])

    sensores = _por_nombre(client.get("/api/sensors"))

    assert sensores["Entrada"]["min_pressure"] == pytest.approx(1.5)
    assert sensores["Entrada"]["max_pressure"] == pytest.approx(6.0)
    assert sensores["Entrada"]["location"] == "Sala técnica"
    assert sensores["Entrada"]["sensor_type"] == "PRESSURE"
    assert sensores["Caldera"]["sensor_type"] == "FLOW"
    assert sensores["Caldera"]["location"] is None


def test_la_ultima_lectura_se_pide_una_sola_vez_por_pagina(client, datos, engine):
    """
    Sin esto, una página de 100 sensores haría 100 consultas a `readings`.
    Se cuentan las consultas que tocan esa tabla durante la petición.
    """
    _entrar(client, datos["admin"])
    consultas = []

    def _contar(conn, cursor, sql, *args):
        if "FROM readings" in sql:
            consultas.append(sql)

    event.listen(engine, "before_cursor_execute", _contar)
    try:
        client.get("/api/sensors")
    finally:
        event.remove(engine, "before_cursor_execute", _contar)

    assert len(consultas) == 1


# ---------------------------------------------------------
# GET /api/sensors/{id}
# ---------------------------------------------------------
def test_un_cliente_ve_su_sensor(client, datos):
    _entrar(client, datos["cliente_a"])

    respuesta = client.get(f"/api/sensors/{datos['entrada'].id}")

    assert respuesta.status_code == 200
    assert respuesta.json()["name"] == "Entrada"
    assert respuesta.json()["status"] == "ONLINE"


def test_un_cliente_no_ve_un_sensor_ajeno(client, datos):
    """404 y no 403: no se confirma que el sensor exista."""
    _entrar(client, datos["cliente_a"])

    respuesta = client.get(f"/api/sensors/{datos['salida'].id}")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "SENSOR_NOT_FOUND"


def test_el_admin_ve_un_sensor_de_cualquier_organizacion(client, datos):
    _entrar(client, datos["admin"])

    assert client.get(f"/api/sensors/{datos['salida'].id}").status_code == 200


def test_un_sensor_que_no_existe_da_404(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.get(f"/api/sensors/{uuid4()}")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "SENSOR_NOT_FOUND"
