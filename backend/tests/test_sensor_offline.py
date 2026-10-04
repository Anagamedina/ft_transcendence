"""
Alerta SENSOR_OFFLINE (issue #28, segunda parte).

`detectar_sensores_mudos` se prueba directamente, con un `ahora` fijo, sin
esperar al minuto del vigilante. Decisiones de Ana del 04-10-2026: más de
5 minutos sin lecturas, solo sensores activos que hayan mandado alguna vez,
una sola alerta abierta por sensor, CRITICAL, y no se resuelve sola.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.alerts import vigilante
from app.modules.alerts.model import Alert
from app.modules.alerts.offline import detectar_sensores_mudos
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

AHORA = datetime(2026, 10, 4, 12, 0, tzinfo=timezone.utc)


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
def db(engine):
    with Session(engine, expire_on_commit=False) as session:
        yield session


def _organizacion(db, nombre):
    org = Organization(name=nombre)
    db.add(org)
    db.flush()
    site = Site(organization_id=org.id, name=f"Sede de {nombre}")
    db.add(site)
    db.flush()
    return org, site


def _sensor(db, site, nombre, ultima_hace=None, activo=True):
    """`ultima_hace` es cuánto hace que llegó su última lectura; None = nunca."""
    sensor = Sensor(
        site_id=site.id,
        external_id=nombre,
        name=nombre,
        unit="bar",
        low_threshold=Decimal("1.5"),
        high_threshold=Decimal("6"),
        is_active=activo,
    )
    db.add(sensor)
    db.flush()
    if ultima_hace is not None:
        llegada = AHORA - ultima_hace
        db.add(
            Reading(
                sensor_id=sensor.id,
                value=Decimal("3.5"),
                unit="bar",
                recorded_at=llegada,
                created_at=llegada,
            )
        )
    db.commit()
    return sensor


def _alertas(db):
    return db.query(Alert).all()


@pytest.fixture()
def site(db):
    return _organizacion(db, "Cliente A")[1]


# ---------------------------------------------------------
# Qué sensores generan alerta
# ---------------------------------------------------------
def test_un_sensor_callado_10_minutos_abre_una_alerta_critical(db, site):
    sensor = _sensor(db, site, "Entrada", ultima_hace=timedelta(minutes=10))

    abiertas = detectar_sensores_mudos(db, AHORA)

    assert abiertas == 1
    [alerta] = _alertas(db)
    assert alerta.sensor_id == sensor.id
    assert alerta.alert_type == "SENSOR_OFFLINE"
    assert alerta.severity == "CRITICAL"
    assert alerta.status == "ACTIVE"
    assert alerta.message == "Sin lecturas desde el 04-10 a las 11:50 UTC (más de 5 minutos)"


def test_un_sensor_con_una_lectura_reciente_no_abre_nada(db, site):
    _sensor(db, site, "Entrada", ultima_hace=timedelta(seconds=30))

    assert detectar_sensores_mudos(db, AHORA) == 0
    assert _alertas(db) == []


def test_justo_en_el_limite_de_5_minutos_no_es_mudo(db, site):
    """El mismo criterio que el estado del sensor (#25): más de 5 min."""
    _sensor(db, site, "Entrada", ultima_hace=timedelta(minutes=5))

    assert detectar_sensores_mudos(db, AHORA) == 0


def test_un_sensor_que_nunca_ha_mandado_nada_no_abre_alerta(db, site):
    """Uno recién dado de alta todavía no se ha conectado: no se ha perdido."""
    _sensor(db, site, "Nuevo")

    assert detectar_sensores_mudos(db, AHORA) == 0


def test_un_sensor_inactivo_no_abre_alerta(db, site):
    """Si lo han apagado a propósito, que esté callado es lo esperado."""
    _sensor(db, site, "Apagado", ultima_hace=timedelta(hours=1), activo=False)

    assert detectar_sensores_mudos(db, AHORA) == 0


# ---------------------------------------------------------
# Una sola alerta abierta
# ---------------------------------------------------------
def test_si_ya_tiene_una_abierta_no_abre_otra(db, site):
    _sensor(db, site, "Entrada", ultima_hace=timedelta(minutes=10))

    detectar_sensores_mudos(db, AHORA)
    # La siguiente vuelta del vigilante, un minuto después.
    segunda = detectar_sensores_mudos(db, AHORA + timedelta(minutes=1))

    assert segunda == 0
    assert len(_alertas(db)) == 1


def test_si_la_anterior_esta_resuelta_y_sigue_mudo_abre_otra(db, site):
    _sensor(db, site, "Entrada", ultima_hace=timedelta(minutes=10))
    detectar_sensores_mudos(db, AHORA)
    [primera] = _alertas(db)
    primera.status = "RESOLVED"
    primera.resolved_at = AHORA
    db.commit()

    assert detectar_sensores_mudos(db, AHORA + timedelta(minutes=1)) == 1
    assert len(_alertas(db)) == 2


def test_una_alerta_de_presion_abierta_no_impide_la_de_offline(db, site):
    """Son tipos distintos: una LOW_PRESSURE abierta no cuenta como OFFLINE."""
    sensor = _sensor(db, site, "Entrada", ultima_hace=timedelta(minutes=10))
    db.add(
        Alert(
            sensor_id=sensor.id,
            alert_type="LOW_PRESSURE",
            severity="WARNING",
            message="Presión baja",
            status="ACTIVE",
        )
    )
    db.commit()

    assert detectar_sensores_mudos(db, AHORA) == 1


def test_varios_sensores_mudos_abren_una_alerta_cada_uno(db, site):
    _sensor(db, site, "Uno", ultima_hace=timedelta(minutes=10))
    _sensor(db, site, "Dos", ultima_hace=timedelta(hours=3))
    _sensor(db, site, "Bien", ultima_hace=timedelta(seconds=10))

    assert detectar_sensores_mudos(db, AHORA) == 2


# ---------------------------------------------------------
# El vigilante
# ---------------------------------------------------------
def test_una_vuelta_con_un_fallo_no_rompe_la_vigilancia(monkeypatch, engine):
    """Si la base falla un momento, se registra y se sigue."""

    def _revienta(db):
        raise RuntimeError("la base no responde")

    monkeypatch.setattr(vigilante, "SessionLocal", sessionmaker(bind=engine))
    monkeypatch.setattr(vigilante, "detectar_sensores_mudos", _revienta)

    assert vigilante.una_vuelta() == 0


def test_el_vigilante_arranca_y_se_para_con_la_aplicacion(monkeypatch):
    """Con `with TestClient(app)` se ejecuta el lifespan: la vuelta corre."""
    vueltas = []
    monkeypatch.setattr(vigilante, "una_vuelta", lambda: vueltas.append(1) or 0)

    with TestClient(app):
        # Deja pasar un instante para que la tarea dé su primera vuelta.
        asyncio.run(asyncio.sleep(0.2))

    assert len(vueltas) >= 1


# ---------------------------------------------------------
# Se ve en GET /api/alerts, con su alcance
# ---------------------------------------------------------
def test_la_alerta_aparece_en_las_alertas_de_su_organizacion(engine, db):
    _, site_a = _organizacion(db, "Cliente A")
    _, site_b = _organizacion(db, "Cliente B")
    _sensor(db, site_a, "Entrada A", ultima_hace=timedelta(minutes=10))
    _sensor(db, site_b, "Entrada B", ultima_hace=timedelta(minutes=10))
    org_a = db.get(Site, site_a.id).organization_id
    cliente = User(
        organization_id=org_a,
        email="a@aquaguard.dev",
        name="a",
        password_hash="da-igual-aqui",
        role="client",
    )
    db.add(cliente)
    db.commit()
    detectar_sensores_mudos(db, AHORA)

    def _get_db():
        s = Session(engine, expire_on_commit=False)
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _get_db
    try:
        client = TestClient(app)
        client.cookies.set(SESSION_COOKIE, create_session_token(cliente.id))
        cuerpo = client.get("/api/alerts").json()
    finally:
        app.dependency_overrides.clear()

    assert cuerpo["total"] == 1
    assert cuerpo["items"][0]["type"] == "SENSOR_OFFLINE"
    assert cuerpo["items"][0]["severity"] == "CRITICAL"
