"""
`GET /api/sensors/{id}/readings` — histórico de un sensor (issue #25).

El test que de verdad importa aquí es el del aislamiento entre
organizaciones: que alguien de un cliente no pueda leerse el histórico de
otro acertando un identificador. Lo demás es paginación.
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
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


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def _montar_cliente(session, nombre, lecturas=0):
    """Una organización con su sede, su sensor, su usuario y sus lecturas."""
    organization = Organization(name=nombre)
    session.add(organization)
    session.flush()

    site = Site(organization_id=organization.id, name=f"Sede de {nombre}")
    session.add(site)
    session.flush()

    sensor = Sensor(
        site_id=site.id,
        external_id=f"SENS-{nombre}",
        name=f"Sensor de {nombre}",
        unit="bar",
    )
    session.add(sensor)

    # El rol va en mayúsculas porque lo exige el CheckConstraint de la
    # tabla. El contrato los declara en minúsculas: es el desajuste de la
    # issue #74, que aquí no molesta.
    user = User(
        organization_id=organization.id,
        email=f"{nombre}@aquaguard.dev".lower(),
        password_hash="da-igual-aqui",
        role="CLIENT",
    )
    session.add(user)
    session.flush()

    base = datetime(2026, 9, 26, 9, 0, tzinfo=timezone.utc)
    for i in range(lecturas):
        session.add(
            Reading(
                sensor_id=sensor.id,
                value=3 + i * 0.1,
                unit="bar",
                recorded_at=base + timedelta(minutes=i),
            )
        )
    session.flush()
    return sensor, user


@pytest.fixture()
def datos(engine):
    """Dos clientes distintos, cada uno con su sensor y sus lecturas."""
    with Session(engine, expire_on_commit=False) as session:
        sensor_a, user_a = _montar_cliente(session, "ClienteA", lecturas=5)
        sensor_b, user_b = _montar_cliente(session, "ClienteB", lecturas=3)
        session.commit()
        return {"a": (sensor_a, user_a), "b": (sensor_b, user_b)}


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


def test_devuelve_el_historico_de_mi_sensor(client, datos):
    sensor, user = datos["a"]
    _entrar(client, user)

    respuesta = client.get(f"/api/sensors/{sensor.id}/readings")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 5
    assert len(cuerpo["items"]) == 5
    assert all(i["sensor_id"] == str(sensor.id) for i in cuerpo["items"])


def test_no_puedo_leer_el_historico_de_otra_organizacion(client, datos):
    """
    El test que sostiene el aislamiento entre clientes.

    El usuario de A pide el sensor de B con su id correcto. Tiene que
    responder 404, igual que un sensor inventado: decirle «existe pero no
    es tuyo» ya le confirma que ese identificador es real.
    """
    sensor_ajeno, _ = datos["b"]
    _, user_a = datos["a"]
    _entrar(client, user_a)

    respuesta = client.get(f"/api/sensors/{sensor_ajeno.id}/readings")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "SENSOR_NOT_FOUND"


def test_un_sensor_inventado_da_404(client, datos):
    _, user = datos["a"]
    _entrar(client, user)

    respuesta = client.get(f"/api/sensors/{uuid4()}/readings")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "SENSOR_NOT_FOUND"


def test_sin_sesion_da_401(client, datos):
    sensor, _ = datos["a"]

    respuesta = client.get(f"/api/sensors/{sensor.id}/readings")

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "UNAUTHORIZED"


def test_un_sensor_sin_lecturas_da_pagina_vacia_no_404(client, engine):
    """
    «Todavía no ha medido» y «no es tuyo» son cosas distintas y se pintan
    distinto. Un sensor propio sin lecturas devuelve 200 con cero items.
    """
    with Session(engine, expire_on_commit=False) as session:
        sensor, user = _montar_cliente(session, "ClienteC", lecturas=0)
        session.commit()

    _entrar(client, user)
    respuesta = client.get(f"/api/sensors/{sensor.id}/readings")

    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 0
    assert respuesta.json()["items"] == []


def test_la_paginacion_parte_el_resultado(client, datos):
    sensor, user = datos["a"]
    _entrar(client, user)

    primera = client.get(
        f"/api/sensors/{sensor.id}/readings", params={"page": 1, "page_size": 2}
    ).json()

    assert primera["total"] == 5
    assert primera["page"] == 1
    assert primera["page_size"] == 2
    assert primera["pages"] == 3  # 5 lecturas de dos en dos son tres páginas
    assert len(primera["items"]) == 2


def test_la_segunda_pagina_trae_lecturas_distintas(client, datos):
    sensor, user = datos["a"]
    _entrar(client, user)

    def ids(page):
        return {
            i["id"]
            for i in client.get(
                f"/api/sensors/{sensor.id}/readings",
                params={"page": page, "page_size": 2},
            ).json()["items"]
        }

    assert ids(1).isdisjoint(ids(2))
