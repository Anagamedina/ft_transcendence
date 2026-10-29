"""
Prueba caducada: solo lectura (B12, issue #146).

Criterios de la issue:

- Con la prueba vencida, las escrituras responden 403 `TRIAL_EXPIRED` y
  las lecturas funcionan.
- Al ampliar la prueba o hacerse cliente, se puede volver a escribir.
- No hay tareas periódicas: la caducidad se calcula en cada petición con
  `trial_ends_at`.

La regla va ruta a ruta, así que hay un test que recorre todas las
escrituras de la API: una ruta nueva que se olvide de ella falla aquí.
"""

import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token, hash_password
from app.main import app
from app.modules.alerts.model import Alert
from app.modules.organizations.model import Organization
from app.modules.sensors.model import Sensor
from app.modules.organizations.trial import trial_expired
from app.modules.sites.model import Site
from app.modules.users.model import User

PASSWORD = "una-contraseña-larga"
NUEVA = "otra-contraseña-muy-larga"


# ---------------------------------------------------------
# DATOS
# ---------------------------------------------------------
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
    """
    Hotel Mar: en prueba, vencida ayer, con un edificio, un sensor, una
    alerta abierta y su cliente. Más un admin sin organización.
    """
    with Session(engine, expire_on_commit=False) as s:
        mar = Organization(
            name="Hotel Mar",
            status="TRIAL",
            trial_ends_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        s.add(mar)
        s.flush()

        torre = Site(organization_id=mar.id, name="Torre")
        s.add(torre)
        s.flush()

        sensor = Sensor(
            site_id=torre.id,
            external_id="S-1",
            name="Sensor 1",
            unit="bar",
            low_threshold=Decimal("1"),
            high_threshold=Decimal("9"),
        )
        s.add(sensor)
        s.flush()

        alerta = Alert(
            sensor_id=sensor.id,
            alert_type="LOW_PRESSURE",
            severity="WARNING",
            message="Presión baja",
            status="ACTIVE",
        )
        cliente = User(
            organization_id=mar.id,
            email="cliente@mar.dev",
            name="Cliente Mar",
            password_hash=hash_password(PASSWORD),
            role="client",
        )
        admin = User(
            email="admin@aquaguard.dev",
            name="Admin",
            password_hash=hash_password(PASSWORD),
            role="admin",
        )
        s.add_all([alerta, cliente, admin])
        s.commit()
        return {"mar": mar, "alerta": alerta, "cliente": cliente, "admin": admin}


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


@pytest.fixture()
def cliente(client, datos):
    return _entrar(client, datos["cliente"])


def _como_admin(datos, accion):
    """El admin actúa desde otro navegador, sin tocar la cookie del cliente."""
    otro = _entrar(TestClient(app), datos["admin"])
    respuesta = otro.post(f"/api/organizations/{datos['mar'].id}/{accion}")
    assert respuesta.status_code == 200, respuesta.text


def _cambiar_fin(engine, datos, fin):
    with Session(engine) as s:
        s.get(Organization, datos["mar"].id).trial_ends_at = fin
        s.commit()


def _codigo(respuesta):
    return respuesta.json()["error"]["code"]


def _escrituras(datos):
    """Todas las escrituras que puede intentar un cliente."""
    alerta = datos["alerta"].id
    return [
        ("PATCH", f"/api/alerts/{alerta}/acknowledge", {}),
        ("PATCH", "/api/me", {"json": {"name": "Otro nombre"}}),
        (
            "POST",
            "/api/me/password",
            {"json": {"current_password": PASSWORD, "new_password": NUEVA}},
        ),
        ("DELETE", f"/api/documents/{uuid4()}", {}),
        (
            "POST",
            "/api/documents",
            {
                "files": {"file": ("plano.pdf", b"%PDF-1.4", "application/pdf")},
                "data": {"site_id": str(uuid4()), "kind": "PLAN"},
            },
        ),
    ]


# ---------------------------------------------------------
# CON LA PRUEBA VENCIDA
# ---------------------------------------------------------
@pytest.mark.parametrize(
    "ruta",
    [
        "/api/me",
        "/api/sites",
        "/api/sensors",
        "/api/alerts",
        "/api/documents",
        "/api/analytics/overview",
    ],
)
def test_las_lecturas_siguen_funcionando(cliente, ruta):
    assert cliente.get(ruta).status_code == 200


def test_me_devuelve_el_fin_de_la_prueba(cliente, datos):
    organizacion = cliente.get("/api/me").json()["organization"]

    assert organizacion["status"] == "TRIAL"
    assert organizacion["trial_ends_at"] is not None


def test_las_escrituras_responden_403_trial_expired(cliente, datos):
    for metodo, ruta, kwargs in _escrituras(datos):
        respuesta = cliente.request(metodo, ruta, **kwargs)

        assert respuesta.status_code == 403, (metodo, ruta, respuesta.text)
        assert _codigo(respuesta) == "TRIAL_EXPIRED", (metodo, ruta)


_SIEMPRE_ABIERTAS = {
    "/api/readings",
    "/api/me/organization/subscribe",
    "/api/me/deletion-request",
    "/api/invitations/by-code/{code}/accept",
}


def _todas_las_escrituras():
    """
    Cada POST, PUT, PATCH y DELETE de la API, salvo los que no piden
    sesión o tienen que funcionar siempre: `auth` (login, logout,
    registro), aceptar una invitación pública (B4), la ingesta del
    simulador, contratar un plan (B14) y pedir la baja (B15). Estas dos
    últimas tienen que funcionar también con la prueba vencida.

    La API pública (`/api/public/`) tampoco usa sesión, sino API key: su
    `TRIAL_EXPIRED` lo prueba `test_public_api.py`.
    """
    for ruta in app.routes:
        if not isinstance(ruta, APIRoute):
            continue
        if ruta.path.startswith(("/api/auth/", "/api/public/")):
            continue
        if ruta.path in _SIEMPRE_ABIERTAS:
            continue
        for metodo in sorted(ruta.methods - {"GET", "HEAD", "OPTIONS"}):
            yield metodo, ruta.path


def test_ninguna_escritura_de_la_api_se_cuela(cliente):
    """
    Un cliente con la prueba vencida no escribe por ninguna ruta: o es
    suya y responde `TRIAL_EXPIRED`, o es de admin y responde `FORBIDDEN`.
    Nunca un 2xx, ni un 404 o 422 que diga que ha llegado a intentarlo.
    """
    escrituras = list(_todas_las_escrituras())
    assert escrituras, "no se ha encontrado ninguna escritura"

    for metodo, plantilla in escrituras:
        ruta = re.sub(r"\{[^}]+\}", str(uuid4()), plantilla)
        respuesta = cliente.request(metodo, ruta, json={})

        assert respuesta.status_code == 403, (metodo, plantilla, respuesta.text)
        assert _codigo(respuesta) in {"TRIAL_EXPIRED", "FORBIDDEN"}, (metodo, plantilla)


@pytest.mark.parametrize(
    "metodo, ruta",
    [
        ("POST", "/api/sites"),
        ("POST", "/api/sensors"),
        ("POST", "/api/organizations/{org}/extend-trial"),
    ],
)
def test_en_una_escritura_de_admin_gana_forbidden(cliente, datos, metodo, ruta):
    # Un TRIAL_EXPIRED aquí le diría que podrá hacerlo cuando le amplíen.
    respuesta = cliente.request(
        metodo, ruta.format(org=datos["mar"].id), json={}
    )

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "FORBIDDEN"


def test_la_escritura_rechazada_no_cambia_nada(cliente, datos, engine):
    cliente.patch(f"/api/alerts/{datos['alerta'].id}/resolve")
    cliente.patch("/api/me", json={"name": "Otro nombre"})

    with Session(engine) as s:
        assert s.get(Alert, datos["alerta"].id).status == "ACTIVE"
        assert s.get(User, datos["cliente"].id).name == "Cliente Mar"


def test_se_puede_cerrar_sesion(cliente):
    assert cliente.post("/api/auth/logout").status_code == 200


def test_con_la_prueba_vencida_se_puede_contratar_un_plan(cliente, datos):
    """Es la salida de la solo lectura: no puede llevar `require_trial_not_expired`."""
    respuesta = cliente.post(
        "/api/me/organization/subscribe",
        json={
            "sites": 1,
            "sensors": 5,
            "billing_period": "MONTHLY",
            "legal_name": "Hotel Mar S.L.",
            "tax_id": "B12345678",
            "billing_address": "Passeig Marítim 1",
            "postal_code": "08003",
            "city": "Barcelona",
            "billing_email": "facturas@mar.dev",
            "iban": "ES91 2100 0418 4502 0005 1332",
            "accept_terms": True,
            "accept_sepa": True,
        },
    )

    assert respuesta.status_code == 200, respuesta.text
    assert respuesta.json()["status"] == "ACTIVE"
    # Ya es cliente: vuelve a poder escribir.
    assert cliente.patch("/api/me", json={"name": "Otro nombre"}).status_code == 200


def test_se_puede_entrar(client, datos):
    respuesta = client.post(
        "/api/auth/login", json={"email": "cliente@mar.dev", "password": PASSWORD}
    )
    assert respuesta.status_code == 200


def test_el_admin_no_se_bloquea(client, datos):
    admin = _entrar(client, datos["admin"])

    respuesta = admin.patch(f"/api/alerts/{datos['alerta'].id}/acknowledge")

    assert respuesta.status_code == 200


def test_una_organizacion_suspendida_sigue_dando_account_disabled(cliente, datos):
    _como_admin(datos, "suspend")

    respuesta = cliente.patch("/api/me", json={"name": "Otro nombre"})

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "ACCOUNT_DISABLED"


# ---------------------------------------------------------
# AMPLIAR DEVUELVE LA ESCRITURA (hacerse cliente: más abajo)
# ---------------------------------------------------------
def test_al_ampliar_se_puede_volver_a_escribir(cliente, datos):
    ruta = f"/api/alerts/{datos['alerta'].id}/acknowledge"
    assert cliente.patch(ruta).status_code == 403

    _como_admin(datos, "extend-trial")

    assert cliente.patch(ruta).status_code == 200


def test_con_la_prueba_en_curso_se_puede_escribir(cliente, datos, engine):
    _cambiar_fin(engine, datos, datetime.now(timezone.utc) + timedelta(days=3))

    respuesta = cliente.patch("/api/me", json={"name": "Otro nombre"})

    assert respuesta.status_code == 200


# ---------------------------------------------------------
# CUÁNDO VENCE
# ---------------------------------------------------------
AHORA = datetime(2026, 10, 14, 12, 0, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "status, fin, vencida",
    [
        ("TRIAL", AHORA - timedelta(seconds=1), True),
        ("TRIAL", AHORA, True),
        ("TRIAL", AHORA + timedelta(seconds=1), False),
        # sqlite devuelve las fechas sin zona; se guardan en UTC.
        ("TRIAL", (AHORA - timedelta(days=1)).replace(tzinfo=None), True),
        ("TRIAL", None, False),
        ("ACTIVE", None, False),
        # Una suspendida que estaba en prueba conserva `trial_ends_at`; la
        # corta `ACCOUNT_DISABLED`, no esta regla.
        ("SUSPENDED", AHORA - timedelta(days=1), False),
    ],
)
def test_cuando_vence_la_prueba(status, fin, vencida):
    organizacion = Organization(name="X", status=status, trial_ends_at=fin)

    assert trial_expired(organizacion, ahora=AHORA) is vencida


def test_sin_organizacion_no_hay_prueba_que_vencer():
    assert trial_expired(None, ahora=AHORA) is False


# ---------------------------------------------------------
# OPENAPI
# ---------------------------------------------------------
@pytest.mark.parametrize(
    "metodo, ruta",
    [
        ("patch", "/api/alerts/{alert_id}/acknowledge"),
        ("patch", "/api/me"),
        ("post", "/api/me/password"),
        ("post", "/api/documents"),
        ("delete", "/api/documents/{document_id}"),
    ],
)
def test_openapi_documenta_trial_expired_en_las_escrituras_de_cliente(metodo, ruta):
    assert "TRIAL_EXPIRED" in _descripcion_403(metodo, ruta)


@pytest.mark.parametrize("metodo, ruta", [("get", "/api/me"), ("post", "/api/sites")])
def test_openapi_no_lo_documenta_donde_no_aplica(metodo, ruta):
    assert "TRIAL_EXPIRED" not in _descripcion_403(metodo, ruta)


def _descripcion_403(metodo, ruta):
    operacion = app.openapi()["paths"][ruta][metodo]
    return operacion.get("responses", {}).get("403", {}).get("description", "")
