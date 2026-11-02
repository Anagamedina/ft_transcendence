"""
Invitaciones (B4, issue #141).

Lo que más importa: el admin invita, el invitado acepta con un enlace de
un solo uso y entra ya con sesión, la invitación caduca a los 7 días
(410) y el código nunca se guarda en claro.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.app_config import app_settings
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.invitations.model import Invitation
from app.modules.invitations.service import hash_code
from app.modules.organizations.model import Organization
from app.modules.users.model import User

PASSWORD = "agua-que-no-se-escapa"


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
    with Session(engine, expire_on_commit=False) as s:
        hotel = Organization(name="Hotel Mar", status="ACTIVE")
        cerrado = Organization(name="Hotel Cerrado", status="SUSPENDED")
        s.add_all([hotel, cerrado])
        s.flush()
        admin = User(email="admin@aquaguard.dev", name="Ana Medina",
                     password_hash="x", role="admin")
        cliente = User(organization_id=hotel.id, email="c@hotelmar.dev",
                       name="Cliente", password_hash="x", role="client")
        s.add_all([admin, cliente])
        s.commit()
        return {"hotel": hotel, "cerrado": cerrado, "admin": admin, "cliente": cliente}


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


def _invitar(client, datos, email="laura@hotelmar.dev", org="hotel"):
    _entrar(client, datos["admin"])
    respuesta = client.post(
        "/api/invitations",
        json={"email": email, "organization_id": str(datos[org].id)},
    )
    client.cookies.clear()
    return respuesta


def _aceptar(client, code, **cambios):
    cuerpo = {"name": "Laura Puig", "password": PASSWORD, "accept_terms": True}
    cuerpo.update(cambios)
    return client.post(f"/api/invitations/by-code/{code}/accept", json=cuerpo)


def _caducar(engine, invitation_id):
    with Session(engine) as s:
        inv = s.get(Invitation, UUID(str(invitation_id)))
        inv.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        s.commit()


def _codigo(respuesta):
    return respuesta.json()["error"]["code"]


# ---------------------------------------------------------
# INVITAR
# ---------------------------------------------------------
def test_el_admin_invita_y_recibe_el_codigo_y_el_enlace(client, datos, engine):
    respuesta = _invitar(client, datos, email="Laura@HotelMar.dev")

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["email"] == "laura@hotelmar.dev"
    assert cuerpo["status"] == "PENDING"
    assert cuerpo["organization_name"] == "Hotel Mar"
    assert cuerpo["created_by_name"] == "Ana Medina"
    base = app_settings.PUBLIC_BASE_URL.rstrip("/")
    assert cuerpo["url"] == f"{base}/registro?invitacion={cuerpo['code']}"

    caduca = datetime.fromisoformat(cuerpo["expires_at"])
    dias = (caduca - datetime.now(timezone.utc)).total_seconds() / 86400
    assert app_settings.INVITATION_TTL_DAYS - 0.01 < dias <= app_settings.INVITATION_TTL_DAYS

    # En la base solo está el hash
    with Session(engine) as s:
        inv = s.get(Invitation, UUID(cuerpo["id"]))
        assert inv.code_hash == hash_code(cuerpo["code"])
        assert cuerpo["code"] not in inv.code_hash


def test_un_cliente_no_puede_invitar(client, datos):
    _entrar(client, datos["cliente"])
    respuesta = client.post(
        "/api/invitations",
        json={"email": "x@hotelmar.dev", "organization_id": str(datos["hotel"].id)},
    )
    assert respuesta.status_code == 403


def test_no_se_invita_a_un_email_con_cuenta(client, datos):
    respuesta = _invitar(client, datos, email="C@hotelmar.dev")
    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "EMAIL_ALREADY_EXISTS"


def test_organizacion_inexistente_da_404(client, datos):
    _entrar(client, datos["admin"])
    respuesta = client.post(
        "/api/invitations",
        json={"email": "x@y.dev", "organization_id": "11111111-1111-4111-8111-111111111111"},
    )
    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "ORGANIZATION_NOT_FOUND"


def test_dos_invitaciones_vigentes_al_mismo_email_dan_409(client, datos):
    assert _invitar(client, datos).status_code == 201
    respuesta = _invitar(client, datos)
    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "INVITATION_ALREADY_PENDING"


def test_si_la_anterior_caduco_se_puede_invitar_otra_vez(client, datos, engine):
    vieja = _invitar(client, datos).json()
    _caducar(engine, vieja["id"])

    nueva = _invitar(client, datos)
    assert nueva.status_code == 201
    with Session(engine) as s:
        assert s.get(Invitation, UUID(vieja["id"])).revoked_at is not None


# ---------------------------------------------------------
# LISTAR, REVOCAR Y REENVIAR
# ---------------------------------------------------------
def test_la_lista_no_lleva_el_codigo_y_filtra_por_estado(client, datos, engine):
    pendiente = _invitar(client, datos, email="a@hotelmar.dev").json()
    caducada = _invitar(client, datos, email="b@hotelmar.dev").json()
    _caducar(engine, caducada["id"])

    _entrar(client, datos["admin"])
    todas = client.get("/api/invitations").json()
    assert todas["total"] == 2
    assert all("code" not in i and "url" not in i for i in todas["items"])

    pendientes = client.get("/api/invitations?status=PENDING").json()
    assert [i["id"] for i in pendientes["items"]] == [pendiente["id"]]
    caducadas = client.get("/api/invitations?status=EXPIRED").json()
    assert [i["id"] for i in caducadas["items"]] == [caducada["id"]]

    otra = client.get(f"/api/invitations?organization_id={datos['cerrado'].id}").json()
    assert otra["total"] == 0


def test_revocar_invalida_el_enlace(client, datos):
    inv = _invitar(client, datos).json()

    _entrar(client, datos["admin"])
    assert client.delete(f"/api/invitations/{inv['id']}").status_code == 204
    # Dos veces no es un error
    assert client.delete(f"/api/invitations/{inv['id']}").status_code == 204
    client.cookies.clear()

    respuesta = client.get(f"/api/invitations/by-code/{inv['code']}")
    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "INVITATION_NOT_FOUND"


def test_reenviar_da_un_codigo_nuevo_y_el_viejo_deja_de_valer(client, datos, engine):
    inv = _invitar(client, datos).json()
    _caducar(engine, inv["id"])

    _entrar(client, datos["admin"])
    nueva = client.post(f"/api/invitations/{inv['id']}/resend")
    client.cookies.clear()

    assert nueva.status_code == 200
    assert nueva.json()["status"] == "PENDING"
    assert nueva.json()["code"] != inv["code"]
    assert client.get(f"/api/invitations/by-code/{inv['code']}").status_code == 404
    assert client.get(f"/api/invitations/by-code/{nueva.json()['code']}").status_code == 200


def test_no_se_reenvia_ni_revoca_una_aceptada(client, datos):
    inv = _invitar(client, datos).json()
    assert _aceptar(client, inv["code"]).status_code == 201

    _entrar(client, datos["admin"])
    reenviar = client.post(f"/api/invitations/{inv['id']}/resend")
    revocar = client.delete(f"/api/invitations/{inv['id']}")
    assert (reenviar.status_code, _codigo(reenviar)) == (409, "INVITATION_NOT_PENDING")
    assert (revocar.status_code, _codigo(revocar)) == (409, "INVITATION_NOT_PENDING")


# ---------------------------------------------------------
# ABRIR EL ENLACE Y ACEPTAR (sin sesión)
# ---------------------------------------------------------
def test_el_enlace_muestra_la_organizacion_y_el_email(client, datos):
    inv = _invitar(client, datos).json()

    respuesta = client.get(f"/api/invitations/by-code/{inv['code']}")

    assert respuesta.status_code == 200
    assert respuesta.json()["organization_name"] == "Hotel Mar"
    assert respuesta.json()["email"] == "laura@hotelmar.dev"


def test_aceptar_crea_el_cliente_y_abre_la_sesion(client, datos, engine):
    inv = _invitar(client, datos).json()

    respuesta = _aceptar(client, inv["code"])

    assert respuesta.status_code == 201
    usuario = respuesta.json()["user"]
    assert usuario["email"] == "laura@hotelmar.dev"
    assert usuario["role"] == "client"
    assert usuario["organization_id"] == str(datos["hotel"].id)
    # La cookie del aceptar ya sirve
    assert client.get("/api/me").json()["user"]["id"] == usuario["id"]

    with Session(engine) as s:
        nuevo = s.get(User, UUID(usuario["id"]))
        assert nuevo.terms_version == app_settings.TERMS_VERSION
        assert nuevo.terms_accepted_at is not None
        assert nuevo.password_hash != PASSWORD
        assert s.get(Invitation, UUID(inv["id"])).accepted_at is not None


def test_el_enlace_es_de_un_solo_uso(client, datos):
    inv = _invitar(client, datos).json()
    assert _aceptar(client, inv["code"]).status_code == 201
    client.cookies.clear()

    segunda = _aceptar(client, inv["code"], name="Otra")
    assert segunda.status_code == 404
    assert _codigo(segunda) == "INVITATION_NOT_FOUND"


def test_una_invitacion_caducada_da_410(client, datos, engine):
    inv = _invitar(client, datos).json()
    _caducar(engine, inv["id"])

    for respuesta in (
        client.get(f"/api/invitations/by-code/{inv['code']}"),
        _aceptar(client, inv["code"]),
    ):
        assert respuesta.status_code == 410
        assert _codigo(respuesta) == "INVITATION_EXPIRED"


def test_a_los_7_dias_ya_no_vale(client, datos, engine):
    """Justo antes de `expires_at` vale; en ese instante, ya no."""
    from app.modules.invitations.service import InvitationService

    inv = _invitar(client, datos).json()
    caduca = datetime.fromisoformat(inv["expires_at"])
    with Session(engine) as s:
        service = InvitationService(s)
        service.get_by_code(inv["code"], ahora=caduca - timedelta(seconds=1))
        with pytest.raises(Exception) as error:
            service.get_by_code(inv["code"], ahora=caduca)
    assert error.value.code == "INVITATION_EXPIRED"


def test_un_codigo_inventado_da_404(client, datos):
    respuesta = client.get("/api/invitations/by-code/no-existe")
    assert respuesta.status_code == 404


@pytest.mark.parametrize(
    ("cambios", "codigo"),
    [
        ({"accept_terms": False}, "TERMS_NOT_ACCEPTED"),
        ({"password": "corta"}, "WEAK_PASSWORD"),
        ({"password": "password1234"}, "WEAK_PASSWORD"),
        ({"password": "laura@hotelmar.dev!!"}, "WEAK_PASSWORD"),
        ({"name": "   "}, "VALIDATION_ERROR"),
    ],
)
def test_datos_incorrectos_dan_422_y_no_gastan_el_enlace(client, datos, engine, cambios, codigo):
    inv = _invitar(client, datos).json()

    respuesta = _aceptar(client, inv["code"], **cambios)

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == codigo
    with Session(engine) as s:
        assert s.get(Invitation, UUID(inv["id"])).accepted_at is None
        assert s.scalar(select(User).where(User.email == "laura@hotelmar.dev")) is None


def test_el_email_no_se_elige_al_aceptar(client, datos):
    inv = _invitar(client, datos).json()
    respuesta = _aceptar(client, inv["code"], email="otro@x.dev")
    assert respuesta.status_code == 422


def test_una_organizacion_suspendida_no_acepta_usuarios(client, datos, engine):
    inv = _invitar(client, datos, org="cerrado").json()

    respuesta = _aceptar(client, inv["code"])

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "ACCOUNT_DISABLED"
    with Session(engine) as s:
        assert s.get(Invitation, UUID(inv["id"])).accepted_at is None
