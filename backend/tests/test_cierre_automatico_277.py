"""
Cierre automático de alertas por las lecturas (#277).

- 15 minutos seguidos de lecturas normales cierran la alerta, con
  `resolved_at` = la primera lectura normal y sin `resolved_by`.
- Menos tiempo, una lectura mala en medio o un sensor callado: sigue abierta.
- Sensor sin conexión que vuelve: se cierra tras 15 minutos enviando.
- Mientras se confirma no se avisa al cliente (#275).
- La API devuelve `normal_since` y `closes_at`.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.alerts import notices
from app.modules.alerts.autoclose import cerrar_por_lecturas
from app.modules.alerts.model import Alert, AlertNotification
from app.modules.alerts.notices import enviar_avisos
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

SALTA = datetime(2026, 10, 25, 10, 0, tzinfo=timezone.utc)


def minuto(m):
    return SALTA + timedelta(minutes=m)


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
def datos(engine):
    with Session(engine, expire_on_commit=False) as session:
        org = Organization(name="Hotel Mar", contact_email="recepcion@hotelmar.dev")
        session.add(org)
        session.flush()
        site = Site(organization_id=org.id, name="Torre A")
        session.add(site)
        session.flush()
        sensor = Sensor(
            site_id=site.id, external_id="SENS-MAR", name="Presión planta 6", unit="bar",
            low_threshold=Decimal("1.500"), high_threshold=Decimal("6.000"),
        )
        session.add(sensor)
        session.flush()
        baja = Alert(
            sensor_id=sensor.id, alert_type="LOW_PRESSURE", severity="CRITICAL",
            message="Presión por debajo del umbral: 0.9 bar (mínimo 1.5)",
            status="ACTIVE", created_at=SALTA,
        )
        session.add(baja)
        admin = User(email="admin@aquaguard.dev", name="Ana", password_hash="x",
                     role="admin", is_active=True)
        session.add(admin)
        session.commit()
        return {"sensor": sensor, "baja": baja, "admin": admin}


def _lecturas(engine, sensor, valores_por_minuto):
    """{minuto: bar} → una lectura por minuto, llegada en ese minuto."""
    with Session(engine) as db:
        for m, valor in valores_por_minuto.items():
            db.add(Reading(sensor_id=sensor.id, value=Decimal(str(valor)), unit="bar",
                           recorded_at=minuto(m), created_at=minuto(m)))
        db.commit()


def _cerrar(engine, ahora):
    with Session(engine) as db:
        return cerrar_por_lecturas(db, ahora=ahora)


def _alerta(engine, alerta):
    with Session(engine) as db:
        return db.get(Alert, alerta.id)


def _utc(fecha):
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------
# PRESIÓN
# ---------------------------------------------------------
def test_15_minutos_normales_la_cierran_con_la_hora_de_la_primera_normal(engine, datos):
    # Mala al saltar y hasta el minuto 9; normal desde el 10
    _lecturas(engine, datos["sensor"], {0: 0.9, 5: 0.8, 9: 1.0, **{m: 3.2 for m in range(10, 26)}})

    assert _cerrar(engine, minuto(25)) == 1

    alerta = _alerta(engine, datos["baja"])
    assert alerta.status == "RESOLVED"
    assert _utc(alerta.resolved_at) == minuto(10)
    assert alerta.resolved_by is None


def test_menos_de_15_minutos_sigue_abierta(engine, datos):
    _lecturas(engine, datos["sensor"], {0: 0.9, **{m: 3.2 for m in range(10, 24)}})

    assert _cerrar(engine, minuto(24)) == 0
    assert _alerta(engine, datos["baja"]).status == "ACTIVE"


def test_una_lectura_mala_en_medio_empieza_la_cuenta_de_cero(engine, datos):
    lecturas = {0: 0.9, **{m: 3.2 for m in range(10, 30)}}
    lecturas[20] = 1.1
    _lecturas(engine, datos["sensor"], lecturas)

    assert _cerrar(engine, minuto(29)) == 0  # normal desde el 21: solo 8 min
    assert _cerrar(engine, minuto(36)) == 0  # sin lecturas desde el 29: callado
    _lecturas(engine, datos["sensor"], {m: 3.2 for m in range(30, 37)})
    assert _cerrar(engine, minuto(36)) == 1
    assert _utc(_alerta(engine, datos["baja"]).resolved_at) == minuto(21)


def test_si_el_sensor_se_calla_no_se_confirma(engine, datos):
    _lecturas(engine, datos["sensor"], {0: 0.9, **{m: 3.2 for m in range(10, 20)}})

    assert _cerrar(engine, minuto(40)) == 0


def test_si_el_admin_corrige_el_limite_las_lecturas_siguientes_cuentan(engine, datos):
    _lecturas(engine, datos["sensor"], {m: 1.3 for m in range(0, 20)})
    with Session(engine) as db:
        db.get(Sensor, datos["sensor"].id).low_threshold = Decimal("1.000")
        db.commit()

    assert _cerrar(engine, minuto(19)) == 1


# ---------------------------------------------------------
# SENSOR SIN CONEXIÓN
# ---------------------------------------------------------
def test_sin_conexion_se_cierra_tras_15_minutos_enviando(engine, datos):
    with Session(engine) as db:
        muda = Alert(sensor_id=datos["sensor"].id, alert_type="SENSOR_OFFLINE",
                     severity="CRITICAL", message="Sin lecturas", status="ACTIVE",
                     created_at=minuto(0))
        db.add(muda)
        db.commit()
        muda_id = muda.id
    # Valores fuera de rango: para esta alerta solo importa que vuelva a mandar
    _lecturas(engine, datos["sensor"], {m: 0.9 for m in range(30, 46)})

    _cerrar(engine, minuto(44))
    with Session(engine) as db:
        assert db.get(Alert, muda_id).status == "ACTIVE"
    _cerrar(engine, minuto(45))
    with Session(engine) as db:
        cerrada = db.get(Alert, muda_id)
        assert cerrada.status == "RESOLVED"
        assert _utc(cerrada.resolved_at) == minuto(30)


# ---------------------------------------------------------
# AVISOS (#275)
# ---------------------------------------------------------
def test_mientras_se_confirma_no_se_avisa_al_cliente(engine, datos, monkeypatch):
    enviados = []
    monkeypatch.setattr(notices, "send_email", lambda to, s, b: enviados.append(to))
    _lecturas(engine, datos["sensor"], {0: 0.9, 3: 3.2, 4: 3.2, 5: 3.2})

    with Session(engine) as db:
        assert enviar_avisos(db, ahora=minuto(5)) == 0
    assert enviados == []
    with Session(engine) as db:
        assert db.scalars(select(AlertNotification)).all() == []


def test_si_vuelve_a_ir_mal_se_avisa(engine, datos, monkeypatch):
    enviados = []
    monkeypatch.setattr(notices, "send_email", lambda to, s, b: enviados.append(to))
    _lecturas(engine, datos["sensor"], {0: 0.9, 3: 3.2, 5: 0.8})

    with Session(engine) as db:
        assert enviar_avisos(db, ahora=minuto(5)) == 1


# ---------------------------------------------------------
# API
# ---------------------------------------------------------
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


def test_la_api_dice_desde_cuando_es_normal_y_cuando_se_cierra(client, engine, datos):
    ahora = datetime.now(timezone.utc).replace(microsecond=0)
    with Session(engine) as db:
        alerta = db.get(Alert, datos["baja"].id)
        alerta.created_at = ahora - timedelta(minutes=10)
        for m, valor in {10: 0.9, 6: 3.2, 1: 3.2}.items():
            db.add(Reading(sensor_id=datos["sensor"].id, value=Decimal(str(valor)), unit="bar",
                           recorded_at=ahora - timedelta(minutes=m),
                           created_at=ahora - timedelta(minutes=m)))
        db.commit()
    client.cookies.set(SESSION_COOKIE, create_session_token(datos["admin"].id))

    [item] = client.get("/api/alerts").json()["items"]

    assert datetime.fromisoformat(item["normal_since"]) == ahora - timedelta(minutes=6)
    assert datetime.fromisoformat(item["closes_at"]) == ahora + timedelta(minutes=9)
    assert item["next_notification_at"] is None


def test_con_lecturas_malas_no_hay_normal_since(client, engine, datos):
    client.cookies.set(SESSION_COOKIE, create_session_token(datos["admin"].id))

    [item] = client.get("/api/alerts").json()["items"]

    assert item["normal_since"] is None and item["closes_at"] is None
