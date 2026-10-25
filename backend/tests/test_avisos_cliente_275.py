"""
Avisos por email al cliente cuando nadie se encarga de una alerta (#275).

- Crítica: email a los 5 min (al contacto) y a los 20 (contacto y usuarios).
- Leve: un solo email a los 60 min.
- «Me encargo» o cerrar para los avisos.
- Uno por vuelta y por alerta, y nunca el mismo dos veces.
- La API devuelve los avisos y cuándo toca el siguiente.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.alerts import notices
from app.modules.alerts.model import Alert, AlertNotification
from app.modules.alerts.notices import enviar_avisos
from app.modules.organizations.model import Organization
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
def emails(monkeypatch):
    """Los emails «enviados»: (destinatario, asunto)."""
    enviados = []
    monkeypatch.setattr(notices, "send_email", lambda to, subject, body: enviados.append((to, subject)))
    return enviados


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
            site_id=site.id,
            external_id="SENS-MAR",
            name="Presión planta 6",
            unit="bar",
            low_threshold=Decimal("1.500"),
            high_threshold=Decimal("6.000"),
        )
        session.add(sensor)
        session.flush()
        critica = Alert(
            sensor_id=sensor.id, alert_type="LOW_PRESSURE", severity="CRITICAL",
            message="Presión por debajo del umbral: 0.4 bar (mínimo 1.5)",
            status="ACTIVE", created_at=SALTA,
        )
        leve = Alert(
            sensor_id=sensor.id, alert_type="HIGH_PRESSURE", severity="WARNING",
            message="Presión por encima del umbral: 6.2 bar (máximo 6)",
            status="ACTIVE", created_at=SALTA,
        )
        session.add_all([critica, leve])
        marta = User(organization_id=org.id, email="marta@hotelmar.dev", name="Marta",
                     password_hash="x", role="client", is_active=True)
        pau = User(organization_id=org.id, email="pau@hotelmar.dev", name="Pau",
                   password_hash="x", role="client", is_active=True)
        baja = User(organization_id=org.id, email="baja@hotelmar.dev", name="Baja",
                    password_hash="x", role="client", is_active=False)
        admin = User(email="admin@aquaguard.dev", name="Ana", password_hash="x", role="admin",
                     is_active=True)
        session.add_all([marta, pau, baja, admin])
        session.commit()
        return {"org": org, "critica": critica, "leve": leve, "marta": marta, "admin": admin}


def _vuelta(engine, ahora):
    with Session(engine) as db:
        return enviar_avisos(db, ahora=ahora)


def _avisos(engine, alerta):
    with Session(engine) as db:
        return db.scalars(
            select(AlertNotification)
            .where(AlertNotification.alert_id == alerta.id)
            .order_by(AlertNotification.attempt)
        ).all()


# ---------------------------------------------------------
# CALENDARIO
# ---------------------------------------------------------
def test_antes_de_los_5_minutos_no_se_avisa(engine, datos, emails):
    assert _vuelta(engine, minuto(4)) == 0
    assert emails == []


def test_critica_primer_email_al_contacto_a_los_5(engine, datos, emails):
    assert _vuelta(engine, minuto(5)) == 1

    assert emails == [("recepcion@hotelmar.dev",
                       "[AquaGuard] Alerta crítica sin atender: Presión baja en Torre A")]
    [aviso] = _avisos(engine, datos["critica"])
    assert (aviso.attempt, aviso.recipient) == (1, "recepcion@hotelmar.dev")


def test_critica_segundo_email_a_contacto_y_usuarios_activos_a_los_20(engine, datos, emails):
    _vuelta(engine, minuto(5))
    emails.clear()

    assert _vuelta(engine, minuto(19)) == 0
    assert _vuelta(engine, minuto(20)) == 1

    assert [to for to, _ in emails] == [
        "recepcion@hotelmar.dev", "marta@hotelmar.dev", "pau@hotelmar.dev",
    ]
    assert emails[0][1].endswith("(2.º aviso)")


def test_critica_no_hay_tercer_email(engine, datos, emails):
    for m in (5, 20, 45, 120):
        _vuelta(engine, minuto(m))

    assert [a.attempt for a in _avisos(engine, datos["critica"])] == [1, 2]


def test_leve_un_solo_email_a_los_60(engine, datos, emails):
    _vuelta(engine, minuto(59))
    assert _avisos(engine, datos["leve"]) == []

    _vuelta(engine, minuto(60))
    _vuelta(engine, minuto(180))
    assert [a.attempt for a in _avisos(engine, datos["leve"])] == [1]


def test_si_el_backend_estuvo_parado_no_envia_dos_de_golpe(engine, datos, emails):
    _vuelta(engine, minuto(30))
    assert [a.attempt for a in _avisos(engine, datos["critica"])] == [1]

    _vuelta(engine, minuto(31))
    assert [a.attempt for a in _avisos(engine, datos["critica"])] == [1, 2]


def test_sin_contacto_el_primero_va_a_los_usuarios(engine, datos, emails):
    with Session(engine) as db:
        db.get(Organization, datos["org"].id).contact_email = None
        db.commit()

    _vuelta(engine, minuto(5))

    assert sorted(to for to, _ in emails) == ["marta@hotelmar.dev", "pau@hotelmar.dev"]


# ---------------------------------------------------------
# PARAR
# ---------------------------------------------------------
@pytest.mark.parametrize("cambio", ["encargarse", "cerrar"])
def test_me_encargo_o_cerrar_paran_los_avisos(engine, datos, emails, cambio):
    _vuelta(engine, minuto(5))
    with Session(engine) as db:
        alerta = db.get(Alert, datos["critica"].id)
        if cambio == "encargarse":
            alerta.acknowledged_at = minuto(10)
        else:
            alerta.status, alerta.resolved_at = "RESOLVED", minuto(10)
        db.commit()

    _vuelta(engine, minuto(20))

    assert [a.attempt for a in _avisos(engine, datos["critica"])] == [1]


# ---------------------------------------------------------
# NUNCA DOS VECES
# ---------------------------------------------------------
def test_repetir_la_vuelta_no_repite_el_aviso(engine, datos, emails):
    _vuelta(engine, minuto(5))
    _vuelta(engine, minuto(6))

    assert len([e for e in emails if "crítica" in e[1]]) == 1


def test_la_base_no_deja_apuntar_el_mismo_aviso_dos_veces(engine, datos):
    with Session(engine) as db:
        for _ in range(2):
            db.add(AlertNotification(alert_id=datos["critica"].id, attempt=1,
                                     recipient="x@y.es", sent_at=SALTA))
        with pytest.raises(IntegrityError):
            db.commit()


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


def _item(client, user, alerta):
    client.cookies.set(SESSION_COOKIE, create_session_token(user.id))
    items = client.get("/api/alerts", params={"page_size": 100}).json()["items"]
    return next(i for i in items if i["id"] == str(alerta.id))


def test_la_api_devuelve_los_avisos_y_el_siguiente(client, engine, datos, emails):
    _vuelta(engine, minuto(5))

    item = _item(client, datos["admin"], datos["critica"])

    assert [(n["attempt"], n["channel"], n["recipient"]) for n in item["notifications"]] == [
        (1, "EMAIL", "recepcion@hotelmar.dev"),
    ]
    siguiente = datetime.fromisoformat(item["next_notification_at"])
    assert siguiente == minuto(20)


def test_sin_avisos_la_lista_esta_vacia_y_al_encargarse_no_hay_siguiente(client, datos):
    assert _item(client, datos["admin"], datos["leve"])["notifications"] == []

    client.cookies.set(SESSION_COOKIE, create_session_token(datos["marta"].id))
    client.patch(f"/api/alerts/{datos['critica'].id}/acknowledge")

    assert _item(client, datos["marta"], datos["critica"])["next_notification_at"] is None
