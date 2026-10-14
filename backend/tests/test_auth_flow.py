"""
Login, registro y `/api/me` (issue #26).

El flujo completo contra la aplicación real: entrar, saber quién eres y
salir. El registro, público desde la B10, se prueba en `test_registro_b10.py`.
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
    assert respuesta.json()["organization"]["name"] == "Hotel Barcelo"
    assert "last_login_at" in respuesta.json()
    assert "terms_version" in respuesta.json()


def test_me_permite_actualizar_el_nombre(client, datos):
    _login(client, "cliente@aquaguard.dev")

    respuesta = client.patch("/api/me", json={"name": "Nuevo nombre"})

    assert respuesta.status_code == 200
    assert respuesta.json()["user"]["name"] == "Nuevo nombre"
    assert client.get("/api/me").json()["user"]["name"] == "Nuevo nombre"


def test_me_no_permite_editar_el_email(client, datos):
    _login(client, "cliente@aquaguard.dev")

    respuesta = client.patch(
        "/api/me", json={"name": "Nuevo nombre", "email": "otro@dev.test"}
    )

    assert respuesta.status_code == 422


def test_me_cambio_de_contrasena_y_sesion_actual_siguen_validos(client, datos):
    _login(client, "cliente@aquaguard.dev")

    respuesta = client.post(
        "/api/me/password",
        json={
            "current_password": CONTRASENA,
            "new_password": "otra-contrasena-larga",
        },
    )

    assert respuesta.status_code == 200
    assert client.get("/api/me").status_code == 200

    client.post("/api/auth/logout")
    assert _login(client, "cliente@aquaguard.dev", "otra-contrasena-larga").status_code == 200


def test_me_rechaza_contrasena_actual_incorrecta(client, datos):
    _login(client, "cliente@aquaguard.dev")

    respuesta = client.post(
        "/api/me/password",
        json={
            "current_password": "contraseña-equivocada",
            "new_password": "otra-contrasena-larga",
        },
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "WRONG_PASSWORD"


def test_me_rechaza_contrasena_nueva_debil(client, datos):
    _login(client, "cliente@aquaguard.dev")

    respuesta = client.post(
        "/api/me/password",
        json={"current_password": CONTRASENA, "new_password": "123456789012"},
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "WEAK_PASSWORD"


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
# Desde la B10 el registro es público y tiene su propio archivo:
# `test_registro_b10.py`.
