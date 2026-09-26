"""
Login, registro y `/api/me` (issue #26).

El flujo completo contra la aplicación real: entrar, saber quién eres, dar
de alta a alguien y salir.
"""

import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, hash_password
from app.main import app
from app.modules.organizations.model import Organization
from app.modules.users.model import User

CONTRASENA = "una-contrasena-larga"


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
        org = Organization(name="Hotel Barcelo")
        session.add(org)
        session.flush()

        admin = User(
            organization_id=org.id,
            email="admin@aquaguard.dev",
            name="Ana Medina",
            password_hash=hash_password(CONTRASENA),
            role="admin",
        )
        cliente = User(
            organization_id=org.id,
            email="cliente@aquaguard.dev",
            name="Hotel Barcelo",
            password_hash=hash_password(CONTRASENA),
            role="client",
        )
        session.add_all([admin, cliente])
        session.commit()
        return {"org": org, "admin": admin, "cliente": cliente}


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


def _login(client, email, password=CONTRASENA):
    return client.post("/api/auth/login", json={"email": email, "password": password})


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------
def test_login_correcto_devuelve_el_usuario_y_abre_sesion(client, datos):
    respuesta = _login(client, "admin@aquaguard.dev")

    assert respuesta.status_code == 200
    assert respuesta.json()["user"]["email"] == "admin@aquaguard.dev"
    assert respuesta.json()["user"]["name"] == "Ana Medina"
    assert respuesta.json()["user"]["role"] == "admin"
    assert SESSION_COOKIE in respuesta.headers.get("set-cookie", "")


def test_la_respuesta_no_lleva_el_hash(client, datos):
    """Lo más importante que NO debe salir por la API."""
    cuerpo = _login(client, "admin@aquaguard.dev").json()

    assert "password_hash" not in cuerpo["user"]
    assert "password" not in cuerpo["user"]


def test_la_cookie_de_sesion_es_httponly(client, datos):
    set_cookie = _login(client, "admin@aquaguard.dev").headers.get("set-cookie", "")

    assert "HttpOnly" in set_cookie
    assert "samesite=lax" in set_cookie.lower()


def test_contrasena_incorrecta_da_401(client, datos):
    respuesta = _login(client, "admin@aquaguard.dev", "la-que-no-es")

    assert respuesta.status_code == 401
    assert not respuesta.headers.get("set-cookie")


def test_email_que_no_existe_da_401(client, datos):
    assert _login(client, "nadie@aquaguard.dev").status_code == 401


def test_no_se_distingue_email_inexistente_de_contrasena_mala(client, datos):
    """
    Si los mensajes difirieran, se podría averiguar qué cuentas existen
    probando emails.
    """
    sin_cuenta = _login(client, "nadie@aquaguard.dev").json()["error"]
    mala = _login(client, "admin@aquaguard.dev", "la-que-no-es").json()["error"]

    assert sin_cuenta["message"] == mala["message"]
    assert sin_cuenta["code"] == mala["code"]


def test_tampoco_se_distinguen_por_el_tiempo_que_tardan(client, datos):
    """
    La otra mitad de lo mismo, y la que se olvida. Comprobar una contraseña
    con Argon2 tarda a propósito; si con un email inexistente saltáramos esa
    comprobación, la respuesta llegaría mucho antes y el reloj delataría qué
    cuentas hay.
    """

    def cronometrar(email):
        inicio = time.perf_counter()
        _login(client, email, "la-que-no-es")
        return time.perf_counter() - inicio

    existe = min(cronometrar("admin@aquaguard.dev") for _ in range(3))
    no_existe = min(cronometrar("nadie@aquaguard.dev") for _ in range(3))

    # Con el señuelo van parejos. Sin él, el inexistente sería órdenes de
    # magnitud más rápido; se deja un margen amplio para no depender de la
    # carga de la máquina.
    assert no_existe > existe * 0.5


# ---------------------------------------------------------
# /api/me
# ---------------------------------------------------------
def test_me_devuelve_quien_soy(client, datos):
    _login(client, "cliente@aquaguard.dev")

    respuesta = client.get("/api/me")

    assert respuesta.status_code == 200
    assert respuesta.json()["user"]["email"] == "cliente@aquaguard.dev"
    assert respuesta.json()["user"]["role"] == "client"


def test_me_sin_sesion_da_401(client, datos):
    respuesta = client.get("/api/me")

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "UNAUTHORIZED"


def test_despues_de_salir_me_ya_no_responde(client, datos):
    """El ciclo entero: entrar, estar dentro, salir, quedarse fuera."""
    _login(client, "admin@aquaguard.dev")
    assert client.get("/api/me").status_code == 200

    client.post("/api/auth/logout")
    client.cookies.clear()

    assert client.get("/api/me").status_code == 401


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------
def test_un_admin_puede_dar_de_alta_un_cliente(client, datos):
    _login(client, "admin@aquaguard.dev")

    respuesta = client.post(
        "/api/auth/register",
        json={
            "email": "nuevo@aquaguard.dev",
            "name": "Hotel Nuevo",
            "password": "otra-contrasena-larga",
        },
    )

    assert respuesta.status_code == 201
    creado = respuesta.json()["user"]
    assert creado["email"] == "nuevo@aquaguard.dev"
    assert creado["role"] == "client"
    # Hereda la organización de quien lo da de alta, no la elige él.
    assert creado["organization_id"] == str(datos["org"].id)


def test_el_nuevo_usuario_puede_entrar(client, datos):
    _login(client, "admin@aquaguard.dev")
    client.post(
        "/api/auth/register",
        json={
            "email": "nuevo@aquaguard.dev",
            "name": "Hotel Nuevo",
            "password": "otra-contrasena-larga",
        },
    )
    client.post("/api/auth/logout")
    client.cookies.clear()

    respuesta = _login(client, "nuevo@aquaguard.dev", "otra-contrasena-larga")

    assert respuesta.status_code == 200


def test_un_cliente_no_puede_dar_de_alta_a_nadie(client, datos):
    """No hay registro público: las cuentas las crea un admin."""
    _login(client, "cliente@aquaguard.dev")

    respuesta = client.post(
        "/api/auth/register",
        json={
            "email": "nuevo@aquaguard.dev",
            "name": "Hotel Nuevo",
            "password": "otra-contrasena-larga",
        },
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "FORBIDDEN"


def test_sin_sesion_no_se_puede_registrar(client, datos):
    respuesta = client.post(
        "/api/auth/register",
        json={
            "email": "nuevo@aquaguard.dev",
            "name": "Hotel Nuevo",
            "password": "otra-contrasena-larga",
        },
    )

    assert respuesta.status_code == 401


def test_un_email_repetido_da_409(client, datos):
    _login(client, "admin@aquaguard.dev")

    respuesta = client.post(
        "/api/auth/register",
        json={
            "email": "cliente@aquaguard.dev",
            "name": "Otro",
            "password": "otra-contrasena-larga",
        },
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


def test_la_contrasena_se_guarda_hasheada(client, datos, engine):
    """Nunca en claro, ni siquiera un momento."""
    _login(client, "admin@aquaguard.dev")
    client.post(
        "/api/auth/register",
        json={
            "email": "nuevo@aquaguard.dev",
            "name": "Hotel Nuevo",
            "password": "otra-contrasena-larga",
        },
    )

    with Session(engine) as session:
        guardado = session.query(User).filter_by(email="nuevo@aquaguard.dev").one()

    assert guardado.password_hash != "otra-contrasena-larga"
    assert guardado.password_hash.startswith("$argon2")
