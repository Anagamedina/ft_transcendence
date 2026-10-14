"""
«Hazte cliente» (B14, issue #150).

Cubre el catálogo de planes, quién puede suscribirse, el paso de TRIAL a
ACTIVE con los datos fiscales y que el IBAN nunca se guarda entero.
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.app_config import app_settings
from app.core.database import Base, get_db
from app.core.exceptions import DomainValidationError
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.organizations.model import Organization
from app.modules.subscriptions.service import mask_iban, normalize_tax_id
from app.modules.users.model import User

IBAN = "ES91 2100 0418 4502 0005 1332"
URL = "/api/me/organization/subscribe"


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
    """Luna en prueba, Nube con la prueba caducada y Sol ya cliente."""
    ahora = datetime.now(timezone.utc)
    with Session(engine, expire_on_commit=False) as s:
        luna = Organization(
            name="Colegio Luna", status="TRIAL", trial_ends_at=ahora + timedelta(days=3),
            contact_email="antes@luna.dev",
        )
        nube = Organization(
            name="Gimnasio Nube", status="TRIAL", trial_ends_at=ahora - timedelta(days=1)
        )
        sol = Organization(name="Hotel Sol", status="ACTIVE")
        s.add_all([luna, nube, sol])
        s.flush()
        usuarios = {
            "luna": User(organization_id=luna.id, email="c@luna.dev", name="Luna",
                         password_hash="x", role="client"),
            "nube": User(organization_id=nube.id, email="c@nube.dev", name="Nube",
                         password_hash="x", role="client"),
            "sol": User(organization_id=sol.id, email="c@sol.dev", name="Sol",
                        password_hash="x", role="client"),
            "admin": User(email="admin@aquaguard.dev", name="Admin",
                          password_hash="x", role="admin"),
        }
        s.add_all(usuarios.values())
        s.commit()
        return {"luna": luna, "nube": nube, "sol": sol, **{f"u_{k}": v for k, v in usuarios.items()}}


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


def _cuerpo(**cambios):
    cuerpo = {
        "plan": "PRO",
        "legal_name": "Colegio Luna S.L.",
        "tax_id": "b-1234 5678",
        "billing_address": "Carrer de la Lluna 1, 08001",
        "billing_email": "facturas@luna.dev",
        "iban": IBAN,
        "accept_terms": True,
    }
    cuerpo.update(cambios)
    return cuerpo


def _codigo(respuesta):
    return respuesta.json()["error"]["code"]


# ---------------------------------------------------------
# PLANES
# ---------------------------------------------------------
def test_los_planes_se_ven_sin_sesion(client):
    respuesta = client.get("/api/plans")

    assert respuesta.status_code == 200
    planes = respuesta.json()
    assert [p["id"] for p in planes] == ["BASIC", "PRO", "ENTERPRISE"]
    assert planes[2]["max_sensors"] is None


# ---------------------------------------------------------
# PERMISOS
# ---------------------------------------------------------
def test_sin_sesion_da_401(client, datos):
    assert client.post(URL, json=_cuerpo()).status_code == 401


def test_un_admin_no_puede_suscribirse(client, datos):
    _entrar(client, datos["u_admin"])
    assert client.post(URL, json=_cuerpo()).status_code == 403


def test_un_cliente_ya_activo_recibe_409(client, datos):
    _entrar(client, datos["u_sol"])
    respuesta = client.post(URL, json=_cuerpo())

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "ORGANIZATION_NOT_IN_TRIAL"


# ---------------------------------------------------------
# SUSCRIPCIÓN
# ---------------------------------------------------------
def test_el_cliente_en_prueba_pasa_a_activo(client, datos, engine):
    _entrar(client, datos["u_luna"])
    respuesta = client.post(URL, json=_cuerpo())

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["status"] == "ACTIVE"
    assert cuerpo["plan"] == "PRO"
    assert cuerpo["plan_name"] == "Profesional"
    assert cuerpo["tax_id"] == "B12345678"
    assert cuerpo["iban_masked"] == "ES** **** **** **** **** 1332"
    assert "iban" not in cuerpo
    # El contacto que no llega se queda como estaba
    assert cuerpo["contact_email"] == "antes@luna.dev"

    with Session(engine) as s:
        luna = s.get(Organization, datos["luna"].id)
        assert luna.status == "ACTIVE"
        assert luna.trial_ends_at is None
        assert luna.subscribed_at is not None
        assert luna.billing_address == "Carrer de la Lluna 1, 08001"
        usuario = s.get(User, datos["u_luna"].id)
        assert usuario.terms_version == app_settings.TERMS_VERSION
        assert usuario.terms_accepted_at is not None


def test_el_iban_entero_no_se_guarda_en_ninguna_columna(client, datos, engine):
    _entrar(client, datos["u_luna"])
    client.post(URL, json=_cuerpo())

    with Session(engine) as s:
        luna = s.get(Organization, datos["luna"].id)
        valores = [str(getattr(luna, c.key)) for c in Organization.__table__.columns]
    assert not any("21000418" in v for v in valores)


def test_una_prueba_caducada_tambien_puede_suscribirse(client, datos):
    _entrar(client, datos["u_nube"])
    respuesta = client.post(URL, json=_cuerpo(iban=None, plan="BASIC"))

    assert respuesta.status_code == 200
    assert respuesta.json()["iban_masked"] is None


def test_el_admin_ve_el_plan_en_la_ficha(client, datos):
    _entrar(client, datos["u_luna"])
    client.post(URL, json=_cuerpo())

    _entrar(client, datos["u_admin"])
    ficha = client.get(f"/api/organizations/{datos['luna'].id}").json()
    assert ficha["plan"] == "PRO"
    assert ficha["iban_masked"] == "ES** **** **** **** **** 1332"


# ---------------------------------------------------------
# VALIDACIÓN
# ---------------------------------------------------------
@pytest.mark.parametrize(
    ("cambios", "codigo"),
    [
        ({"accept_terms": False}, "TERMS_NOT_ACCEPTED"),
        ({"tax_id": "B1"}, "INVALID_TAX_ID"),
        ({"iban": "ES00 2100 0418 4502 0005 1332"}, "INVALID_IBAN"),
        ({"iban": "1234"}, "INVALID_IBAN"),
        ({"plan": "GRATIS"}, "VALIDATION_ERROR"),
        ({"billing_email": "no-es-un-email"}, "VALIDATION_ERROR"),
    ],
)
def test_datos_incorrectos_dan_422_y_no_cambian_nada(client, datos, engine, cambios, codigo):
    _entrar(client, datos["u_luna"])
    respuesta = client.post(URL, json=_cuerpo(**cambios))

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == codigo
    with Session(engine) as s:
        assert s.get(Organization, datos["luna"].id).status == "TRIAL"


def test_faltan_los_datos_fiscales(client, datos):
    _entrar(client, datos["u_luna"])
    cuerpo = _cuerpo()
    del cuerpo["legal_name"]

    assert client.post(URL, json=cuerpo).status_code == 422


def test_mask_iban_y_normalize_tax_id():
    assert mask_iban("de89370400440532013000") == "DE** **** **** **** **30 00"
    assert normalize_tax_id(" x-1234567.l ") == "X1234567L"
    with pytest.raises(DomainValidationError):
        mask_iban("ES91 2100 0418 4502 0005 1333")
