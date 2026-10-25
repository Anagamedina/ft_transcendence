"""
Retoques del backend para la página de alertas del admin (#252).

- Solo AquaGuard (admin) cierra alertas: el cliente dice «Me encargo».
- Cada alerta trae el límite que ha cruzado (`threshold`), para pintar
  «1,1 bar · mín. 1,5» sin leerlo del mensaje.
- Cada organización trae cuándo se creó su alerta abierta más antigua
  (`oldest_open_alert_at`), para «la más antigua: 6 h».
- `?q=` busca también por código del sensor, edificio y cliente, no solo
  por nombre del sensor y mensaje.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

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


def _alerta(session, sensor, tipo, estado="ACTIVE", hace=timedelta(0)):
    alerta = Alert(
        sensor_id=sensor.id,
        alert_type=tipo,
        severity="WARNING",
        message=f"{tipo} de prueba",
        status=estado,
        created_at=AHORA - hace,
        resolved_at=AHORA if estado == "RESOLVED" else None,
    )
    session.add(alerta)
    session.flush()
    return alerta


@pytest.fixture()
def datos(engine):
    with Session(engine, expire_on_commit=False) as session:
        con = Organization(name="Hotel Mar")
        sin = Organization(name="Hoteles Sol")
        session.add_all([con, sin])
        session.flush()
        site = Site(organization_id=con.id, name="Torre A")
        session.add(site)
        session.flush()
        sensor = Sensor(
            site_id=site.id,
            external_id="SENS-MAR",
            name="Presión planta 6",
            unit="bar",
            low_threshold=Decimal("1.500"),
            high_threshold=Decimal("6.000"),
        )
        session.add(sensor)
        session.flush()
        alertas = {
            "baja": _alerta(session, sensor, "LOW_PRESSURE", hace=timedelta(minutes=25)),
            "alta": _alerta(session, sensor, "HIGH_PRESSURE", hace=timedelta(hours=2)),
            "muda": _alerta(session, sensor, "SENSOR_OFFLINE", hace=timedelta(minutes=5)),
            # Resuelta y más antigua: no cuenta para «la más antigua abierta».
            "vieja": _alerta(
                session, sensor, "LOW_PRESSURE", estado="RESOLVED", hace=timedelta(days=3)
            ),
        }
        admin = User(email="admin@aquaguard.dev", name="Ana", password_hash="x", role="admin")
        cliente = User(
            organization_id=con.id,
            email="recepcion@hotelmar.dev",
            name="Marta",
            password_hash="x",
            role="client",
        )
        session.add_all([admin, cliente])
        session.commit()
        return {"con": con, "sin": sin, "alertas": alertas, "admin": admin, "cliente": cliente}


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
    return client


# ---------------------------------------------------------
# SOLO AQUAGUARD CIERRA
# ---------------------------------------------------------
def test_el_cliente_se_encarga_pero_no_cierra(client, datos):
    _entrar(client, datos["cliente"])
    alerta = datos["alertas"]["baja"].id

    assert client.patch(f"/api/alerts/{alerta}/acknowledge").status_code == 200
    respuesta = client.patch(f"/api/alerts/{alerta}/resolve")

    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "FORBIDDEN"


def test_el_admin_cierra(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.patch(f"/api/alerts/{datos['alertas']['baja'].id}/resolve")

    assert respuesta.status_code == 200
    assert respuesta.json()["state"] == "RESOLVED"
    assert respuesta.json()["resolved_by_name"] == "Ana"


def test_el_openapi_dice_que_cerrar_es_de_admin(client):
    ruta = client.get("/api/openapi.json").json()["paths"]["/api/alerts/{alert_id}/resolve"]

    assert "403" in ruta["patch"]["responses"]


# ---------------------------------------------------------
# LÍMITE CRUZADO
# ---------------------------------------------------------
@pytest.mark.parametrize(
    ("alerta", "limite"),
    [("baja", 1.5), ("alta", 6.0), ("muda", None)],
)
def test_cada_alerta_trae_el_limite_que_ha_cruzado(client, datos, alerta, limite):
    _entrar(client, datos["admin"])

    items = client.get("/api/alerts", params={"page_size": 100}).json()["items"]
    item = next(i for i in items if i["id"] == str(datos["alertas"][alerta].id))

    assert item["threshold"] == limite


# ---------------------------------------------------------
# LA ALERTA ABIERTA MÁS ANTIGUA DE CADA CLIENTE
# ---------------------------------------------------------
def _organizacion(client, datos, cual):
    items = client.get("/api/organizations", params={"page_size": 100}).json()["items"]
    return next(i for i in items if i["id"] == str(datos[cual].id))


def test_la_mas_antigua_es_la_abierta_mas_vieja(client, datos):
    _entrar(client, datos["admin"])

    org = _organizacion(client, datos, "con")

    mas_antigua = datetime.fromisoformat(org["oldest_open_alert_at"])
    # La de hace 2 h, no la resuelta de hace 3 días.
    assert abs(mas_antigua - (AHORA - timedelta(hours=2))) < timedelta(seconds=5)
    assert org["open_alerts"] == 3


def test_sin_alertas_abiertas_es_nulo(client, datos):
    _entrar(client, datos["admin"])

    assert _organizacion(client, datos, "sin")["oldest_open_alert_at"] is None


def test_al_cerrar_la_mas_antigua_pasa_a_la_siguiente(client, datos):
    _entrar(client, datos["admin"])
    client.patch(f"/api/alerts/{datos['alertas']['alta'].id}/resolve")

    org = _organizacion(client, datos, "con")

    mas_antigua = datetime.fromisoformat(org["oldest_open_alert_at"])
    assert abs(mas_antigua - (AHORA - timedelta(minutes=25))) < timedelta(seconds=5)


# ---------------------------------------------------------
# BUSCAR POR SENSOR, EDIFICIO O CLIENTE
# ---------------------------------------------------------
@pytest.mark.parametrize(
    ("q", "cuantas"),
    [("planta 6", 4), ("sens-mar", 4), ("torre", 4), ("hotel mar", 4), ("hoteles sol", 0), ("offline", 1)],
)
def test_buscar_por_sensor_edificio_o_cliente(client, datos, q, cuantas):
    _entrar(client, datos["admin"])

    respuesta = client.get("/api/alerts", params={"q": q})

    assert respuesta.json()["total"] == cuantas
