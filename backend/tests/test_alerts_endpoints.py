"""
Endpoints de alertas (issue #28, primera parte).

Cubre los tres de lectura y gestión. Las reglas que generan alertas al
recibir una lectura van aparte: tocan `ReadingService.create()`, que está
en otra rama sin mergear.
"""

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.alerts.model import Alert
from app.modules.organizations.model import Organization
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


def _montar_cliente(session, nombre, alertas=0):
    org = Organization(name=nombre)
    session.add(org)
    session.flush()

    site = Site(organization_id=org.id, name=f"Sede de {nombre}")
    session.add(site)
    session.flush()

    sensor = Sensor(
        site_id=site.id,
        external_id=f"SENS-{nombre}",
        name=f"Sensor de {nombre}",
        unit="bar",
    )
    session.add(sensor)

    user = User(
        organization_id=org.id,
        email=f"{nombre}@aquaguard.dev".lower(),
        name=f"Usuario de {nombre}",
        password_hash="da-igual-aqui",
        role="client",
    )
    session.add_all([sensor, user])
    session.flush()

    creadas = []
    for i in range(alertas):
        a = Alert(
            sensor_id=sensor.id,
            alert_type="LOW_PRESSURE",
            severity="WARNING",
            message=f"Presión baja en {nombre} ({i})",
            status="ACTIVE",
        )
        session.add(a)
        creadas.append(a)
    session.flush()
    return sensor, user, creadas


@pytest.fixture()
def datos(engine):
    with Session(engine, expire_on_commit=False) as session:
        sensor_a, user_a, alertas_a = _montar_cliente(session, "ClienteA", alertas=3)
        sensor_b, user_b, alertas_b = _montar_cliente(session, "ClienteB", alertas=2)
        session.commit()
        return {
            "a": {"sensor": sensor_a, "user": user_a, "alertas": alertas_a},
            "b": {"sensor": sensor_b, "user": user_b, "alertas": alertas_b},
        }


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


# ---------------------------------------------------------
# GET /api/alerts
# ---------------------------------------------------------
def test_listo_solo_las_alertas_de_mi_organizacion(client, datos):
    """A tiene 3 y B tiene 2. A no debe ver 5."""
    _entrar(client, datos["a"]["user"])

    cuerpo = client.get("/api/alerts").json()

    assert cuerpo["total"] == 3
    mias = {str(a.id) for a in datos["a"]["alertas"]}
    assert {i["id"] for i in cuerpo["items"]} == mias


def test_el_contrato_llama_type_a_lo_que_la_tabla_llama_alert_type(client, datos):
    _entrar(client, datos["a"]["user"])

    item = client.get("/api/alerts").json()["items"][0]

    assert item["type"] == "LOW_PRESSURE"
    assert "alert_type" not in item


def test_sin_sesion_da_401(client, datos):
    respuesta = client.get("/api/alerts")

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "UNAUTHORIZED"


def test_puedo_filtrar_por_sensor(client, datos):
    _entrar(client, datos["a"]["user"])

    ajeno = datos["b"]["sensor"].id
    cuerpo = client.get("/api/alerts", params={"sensor_id": str(ajeno)}).json()

    # El sensor es de otra organización: no se cuela ninguna.
    assert cuerpo["total"] == 0


def test_puedo_filtrar_por_estado(client, datos):
    _entrar(client, datos["a"]["user"])

    activas = client.get("/api/alerts", params={"status": "ACTIVE"}).json()
    resueltas = client.get("/api/alerts", params={"status": "RESOLVED"}).json()

    assert activas["total"] == 3
    assert resueltas["total"] == 0


# ---------------------------------------------------------
# PATCH acknowledge
# ---------------------------------------------------------
def test_reconocer_deja_constancia_sin_cerrar(client, datos):
    _entrar(client, datos["a"]["user"])
    alerta = datos["a"]["alertas"][0]

    cuerpo = client.patch(f"/api/alerts/{alerta.id}/acknowledge").json()

    assert cuerpo["acknowledged_at"] is not None
    # Reconocer no es resolver: sigue activa.
    assert cuerpo["status"] == "ACTIVE"
    assert cuerpo["resolved_at"] is None


def test_reconocer_dos_veces_no_pisa_la_primera_hora(client, datos, engine):
    """
    Idempotente. Si dos operadores pulsan a la vez, interesa cuándo se
    reconoció por primera vez, no el último clic.
    """
    _entrar(client, datos["a"]["user"])
    alerta = datos["a"]["alertas"][0]

    primera = client.patch(f"/api/alerts/{alerta.id}/acknowledge").json()
    segunda = client.patch(f"/api/alerts/{alerta.id}/acknowledge")

    assert segunda.status_code == 200
    with Session(engine) as s:
        guardada = s.get(Alert, alerta.id)
    assert guardada.acknowledged_at.isoformat()[:19] == primera["acknowledged_at"][:19]


def test_no_puedo_reconocer_una_alerta_de_otra_organizacion(client, datos):
    _entrar(client, datos["a"]["user"])
    ajena = datos["b"]["alertas"][0]

    respuesta = client.patch(f"/api/alerts/{ajena.id}/acknowledge")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "ALERT_NOT_FOUND"


# ---------------------------------------------------------
# PATCH resolve
# ---------------------------------------------------------
def test_resolver_cierra_la_alerta(client, datos):
    _entrar(client, datos["a"]["user"])
    alerta = datos["a"]["alertas"][0]

    cuerpo = client.patch(f"/api/alerts/{alerta.id}/resolve").json()

    assert cuerpo["status"] == "RESOLVED"
    assert cuerpo["resolved_at"] is not None


def test_resolver_dos_veces_da_409(client, datos):
    """
    No es un éxito silencioso: volvería a escribir la fecha de cierre y se
    perdería cuándo se atendió de verdad.
    """
    _entrar(client, datos["a"]["user"])
    alerta = datos["a"]["alertas"][0]
    client.patch(f"/api/alerts/{alerta.id}/resolve")

    respuesta = client.patch(f"/api/alerts/{alerta.id}/resolve")

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "ALERT_ALREADY_RESOLVED"


def test_la_fecha_de_cierre_no_cambia_tras_el_409(client, datos, engine):
    _entrar(client, datos["a"]["user"])
    alerta = datos["a"]["alertas"][0]
    primera = client.patch(f"/api/alerts/{alerta.id}/resolve").json()

    client.patch(f"/api/alerts/{alerta.id}/resolve")

    with Session(engine) as s:
        guardada = s.get(Alert, alerta.id)
    assert guardada.resolved_at.isoformat()[:19] == primera["resolved_at"][:19]


def test_no_puedo_resolver_una_alerta_de_otra_organizacion(client, datos):
    _entrar(client, datos["a"]["user"])
    ajena = datos["b"]["alertas"][0]

    respuesta = client.patch(f"/api/alerts/{ajena.id}/resolve")

    assert respuesta.status_code == 404


def test_una_alerta_que_no_existe_da_404(client, datos):
    from uuid import uuid4

    _entrar(client, datos["a"]["user"])

    assert client.patch(f"/api/alerts/{uuid4()}/resolve").status_code == 404
