"""
Registro público con prueba de 7 días (B10, issue #140).

Criterios de la issue:

- Un visitante se registra sin sesión y entra directamente a su panel.
- Se crea una organización TRIAL que vence a los 7 días.
- Email u organización repetidos responden 409.
- La contraseña débil responde 422.

Más la regla común de contraseñas (`shared/passwords.py`), que reutilizan
la B4 y la B8.
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
from app.core.exceptions import ConflictError, DomainValidationError
from app.core.security import SESSION_COOKIE, hash_password
from app.main import app
from app.modules.auth.schemas import RegisterRequest
from app.modules.auth.service import AuthService
from app.modules.organizations.model import Organization
from app.modules.users.model import User
from app.modules.users.repository import UserRepository
from app.shared.passwords import check_password

CONTRASENA = "agua-que-no-se-escapa"


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
def existente(engine):
    """Una organización y una cuenta que ya existen, para los 409."""
    with Session(engine, expire_on_commit=False) as session:
        org = Organization(name="Hotel Barcelo")
        session.add(org)
        session.flush()
        session.add(
            User(
                organization_id=org.id,
                email="cliente@aquaguard.dev",
                name="Hotel Barcelo",
                password_hash=hash_password(CONTRASENA),
                role="client",
            )
        )
        session.commit()
        return org


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


def _cuerpo(**cambios):
    return {
        "name": "Ana Medina",
        "email": "ana@hotelmar.dev",
        "password": CONTRASENA,
        "organization_name": "Hotel Mar",
        "accept_terms": True,
        **cambios,
    }


def _registrar(client, **cambios):
    return client.post("/api/auth/register", json=_cuerpo(**cambios))


def _codigo(respuesta):
    return respuesta.json()["error"]["code"]


def _contar(engine, modelo):
    with Session(engine) as session:
        return session.query(modelo).count()


# ---------------------------------------------------------
# ALTA
# ---------------------------------------------------------
def test_sin_sesion_se_registra_y_queda_dentro(client, existente):
    respuesta = _registrar(client)

    assert respuesta.status_code == 201
    usuario = respuesta.json()["user"]
    assert usuario["email"] == "ana@hotelmar.dev"
    assert usuario["role"] == "client"
    # Abre la sesión, como el login: la cookie ya sirve para /api/me.
    assert SESSION_COOKIE in respuesta.cookies
    me = client.get("/api/me")
    assert me.status_code == 200
    assert me.json()["user"]["id"] == usuario["id"]


def test_la_cookie_del_registro_es_httponly(client, existente):
    respuesta = _registrar(client)

    assert "httponly" in respuesta.headers["set-cookie"].lower()


def test_crea_una_organizacion_en_prueba_de_7_dias(client, engine, existente):
    antes = datetime.now(timezone.utc)
    respuesta = _registrar(client)
    despues = datetime.now(timezone.utc)

    with Session(engine) as session:
        org_id = UUID(respuesta.json()["user"]["organization_id"])
        org = session.get(Organization, org_id)
        assert org.name == "Hotel Mar"
        assert org.status == "TRIAL"
        # Quien se registra queda como contacto del cliente.
        assert org.contact_email == "ana@hotelmar.dev"
        fin = org.trial_ends_at.replace(tzinfo=timezone.utc)
    dias = timedelta(days=app_settings.TRIAL_DAYS)
    assert antes + dias <= fin <= despues + dias


def test_la_prueba_dura_trial_days(engine, existente, monkeypatch):
    """`TRIAL_DAYS` del .env manda, no un 7 escrito en el código."""
    monkeypatch.setattr(app_settings, "TRIAL_DAYS", 14)
    ahora = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)

    with Session(engine, expire_on_commit=False) as session:
        AuthService(session).register(RegisterRequest(**_cuerpo()), ahora=ahora)
        org = session.query(Organization).filter_by(name="Hotel Mar").one()

    assert org.trial_ends_at.replace(tzinfo=timezone.utc) == ahora + timedelta(days=14)


def test_guarda_la_version_de_los_terminos_aceptados(engine, existente):
    ahora = datetime(2026, 10, 12, 10, 0, tzinfo=timezone.utc)

    with Session(engine, expire_on_commit=False) as session:
        AuthService(session).register(RegisterRequest(**_cuerpo()), ahora=ahora)
        usuario = session.query(User).filter_by(email="ana@hotelmar.dev").one()

    assert usuario.terms_version == app_settings.TERMS_VERSION
    assert usuario.terms_accepted_at.replace(tzinfo=timezone.utc) == ahora


def test_la_contrasena_se_guarda_hasheada(client, engine, existente):
    """Nunca en claro, ni siquiera un momento."""
    _registrar(client)

    with Session(engine) as session:
        guardado = session.query(User).filter_by(email="ana@hotelmar.dev").one()

    assert guardado.password_hash != CONTRASENA
    assert guardado.password_hash.startswith("$argon2")


def test_despues_puede_volver_a_entrar(client, existente):
    _registrar(client)
    client.post("/api/auth/logout")
    client.cookies.clear()

    respuesta = client.post(
        "/api/auth/login", json={"email": "ana@hotelmar.dev", "password": CONTRASENA}
    )

    assert respuesta.status_code == 200


def test_con_sesion_abierta_tambien_crea_una_cuenta_nueva(client, existente):
    """
    Es público para todos: una sesión abierta no cambia nada, y la cuenta
    nueva no hereda la organización de quien estaba dentro.
    """
    client.post(
        "/api/auth/login", json={"email": "cliente@aquaguard.dev", "password": CONTRASENA}
    )

    respuesta = _registrar(client)

    assert respuesta.status_code == 201
    assert respuesta.json()["user"]["organization_id"] != str(existente.id)
    assert client.get("/api/me").json()["user"]["email"] == "ana@hotelmar.dev"


# ---------------------------------------------------------
# 409 — YA EXISTE
# ---------------------------------------------------------
@pytest.mark.parametrize("email", ["cliente@aquaguard.dev", "  Cliente@AquaGuard.dev "])
def test_un_email_repetido_da_409(client, engine, existente, email):
    respuesta = _registrar(client, email=email)

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "EMAIL_ALREADY_EXISTS"
    # Ni organización a medias.
    assert _contar(engine, Organization) == 1


@pytest.mark.parametrize("nombre", ["Hotel Barcelo", "hotel BARCELO"])
def test_una_organizacion_repetida_da_409(client, engine, existente, nombre):
    respuesta = _registrar(client, organization_name=nombre)

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "ORGANIZATION_NAME_TAKEN"
    assert _contar(engine, User) == 1


def test_dos_registros_a_la_vez_con_el_mismo_email_dan_409(
    engine, existente, monkeypatch
):
    """
    Los dos pasan la comprobación del email antes de que el otro guarde, y
    el índice único para al segundo. Tiene que salir el 409, no un 500, y
    sin dejar la organización creada.
    """
    original = UserRepository.get_by_email
    llamadas = []

    def no_lo_ve_la_primera_vez(self, email):
        llamadas.append(email)
        return None if len(llamadas) == 1 else original(self, email)

    monkeypatch.setattr(UserRepository, "get_by_email", no_lo_ve_la_primera_vez)

    with Session(engine, expire_on_commit=False) as session:
        with pytest.raises(ConflictError) as error:
            AuthService(session).register(
                RegisterRequest(**_cuerpo(email="cliente@aquaguard.dev"))
            )

    assert error.value.code == "EMAIL_ALREADY_EXISTS"
    assert _contar(engine, Organization) == 1


# ---------------------------------------------------------
# 422 — DATOS QUE NO VALEN
# ---------------------------------------------------------
def test_sin_aceptar_los_terminos_da_422(client, engine, existente):
    respuesta = _registrar(client, accept_terms=False)

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "TERMS_NOT_ACCEPTED"
    assert _contar(engine, User) == 1


@pytest.mark.parametrize(
    "password",
    [
        "corta-11-ch",  # 11 caracteres
        "123456789012",  # común
        "Password1234",  # común, aunque cambien las mayúsculas
        "aaaaaaaaaaaaaaaa",  # siempre lo mismo
        "121212121212",
        "ana.medina-2026",  # contiene el usuario del email
        "abcde" * 26,  # 130: más de 128, la corta el schema
    ],
)
def test_una_contrasena_debil_da_422(client, engine, existente, password):
    respuesta = _registrar(client, email="ana.medina@hotelmar.dev", password=password)

    assert respuesta.status_code == 422
    assert _codigo(respuesta) in {"WEAK_PASSWORD", "VALIDATION_ERROR"}
    assert _contar(engine, User) == 1


def test_la_contrasena_debil_explica_que_falla(client, existente):
    respuesta = _registrar(client, password="corta")

    assert _codigo(respuesta) == "WEAK_PASSWORD"
    assert "12" in respuesta.json()["error"]["message"]


@pytest.mark.parametrize("nombre", ["", "   "])
def test_una_organizacion_sin_nombre_da_422(client, existente, nombre):
    respuesta = _registrar(client, organization_name=nombre)

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "INVALID_NAME"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("organization_name", "Hotel Mar!"), ("organization_name", "Hotel <Spa>"),
     ("name", "Ana 2"), ("name", "ana@hotelmar.dev")],
)
def test_un_nombre_con_signos_da_422_en_su_campo(client, existente, campo, valor):
    respuesta = _registrar(client, **{campo: valor})

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "INVALID_NAME"
    assert respuesta.json()["error"]["details"][0]["field"] == campo


def test_los_nombres_se_guardan_sin_espacios_de_mas(client, engine, existente):
    respuesta = _registrar(
        client, name="  Ana   Medina ", organization_name=" Ca n'Oller,   S.L. "
    )

    assert respuesta.status_code == 201
    with Session(engine) as s:
        organizacion = s.scalar(
            select(Organization).where(Organization.name == "Ca n'Oller, S.L.")
        )
        assert organizacion is not None
        assert s.scalar(select(User).where(User.email == "ana@hotelmar.dev")).name == "Ana Medina"


@pytest.mark.parametrize("falta", ["name", "email", "password", "organization_name", "accept_terms"])
def test_falta_un_campo_da_422(client, existente, falta):
    cuerpo = _cuerpo()
    del cuerpo[falta]

    respuesta = client.post("/api/auth/register", json=cuerpo)

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "VALIDATION_ERROR"


def test_ya_no_acepta_organization_id(client, existente):
    """El alta de un cliente en otra organización era la ruta antigua."""
    respuesta = _registrar(client, organization_id=str(existente.id))

    assert respuesta.status_code == 422


# ---------------------------------------------------------
# REGLA COMÚN DE CONTRASEÑAS (B4 y B8 la reutilizan)
# ---------------------------------------------------------
@pytest.mark.parametrize(
    "password",
    ["agua-que-no-se-escapa", "una-contrasena-larga", "Tr3s.tristes.tigres", "abcde" * 25 + "xyz"],
)
def test_contrasenas_que_valen(password):
    check_password(password, email="ana@hotelmar.dev")


def test_un_usuario_de_email_corto_no_bloquea_contrasenas():
    """«ana» aparece en muchas contraseñas sin tener que ver con el email."""
    check_password("mañana-llueve-mucho", email="ana@hotelmar.dev")


def test_tampoco_puede_contener_el_email_entero():
    with pytest.raises(DomainValidationError) as error:
        check_password("x-ana@hotelmar.dev-x", email="ana@hotelmar.dev")

    assert error.value.code == "WEAK_PASSWORD"
