"""
`POST /api/auth/logout` (issue #26).

Lo que se comprueba aquí es sobre todo que la cookie se borre **de verdad**
en el navegador. Es fácil escribir un logout que responda 200 y deje la
sesión abierta, y el usuario no tiene forma de notarlo hasta que descubre
que sigue dentro.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.organizations.model import Organization
from app.modules.users.model import User


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
def usuario(engine):
    with Session(engine, expire_on_commit=False) as session:
        organization = Organization(name="Hotel Barcelo")
        session.add(organization)
        session.flush()
        user = User(
            organization_id=organization.id,
            email="ana@aquaguard.dev",
            name="Ana Medina",
            password_hash="da-igual-aqui",
            role="admin",
        )
        session.add(user)
        session.commit()
        return user


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


def test_logout_responde_200_con_su_mensaje(client):
    respuesta = client.post("/api/auth/logout")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"message": "Sesión cerrada."}


def test_logout_borra_la_cookie(client, usuario):
    """
    La comprobación que importa: que salga un Set-Cookie que la vacía.

    Un logout que devuelve 200 sin tocar la cookie parece funcionar y deja
    la sesión abierta.
    """
    client.cookies.set(SESSION_COOKIE, create_session_token(usuario.id))

    respuesta = client.post("/api/auth/logout")

    set_cookie = respuesta.headers.get("set-cookie", "")
    assert SESSION_COOKIE in set_cookie
    assert 'aquaguard_session=""' in set_cookie or "aquaguard_session=;" in set_cookie


def test_la_cookie_borrada_conserva_sus_atributos(client, usuario):
    """
    Borrar una cookie exige repetir los atributos con los que se puso. Con
    un `path` distinto, el navegador la trata como otra y no la borra.
    """
    client.cookies.set(SESSION_COOKIE, create_session_token(usuario.id))

    set_cookie = client.post("/api/auth/logout").headers.get("set-cookie", "")

    assert "HttpOnly" in set_cookie
    assert "Path=/" in set_cookie
    assert "samesite=lax" in set_cookie.lower()


def test_se_puede_salir_sin_haber_entrado(client):
    """
    No exige sesión a propósito: quien más necesita salir es justo quien
    tiene la sesión en mal estado.
    """
    assert client.post("/api/auth/logout").status_code == 200


def test_se_puede_salir_con_una_cookie_estropeada(client):
    client.cookies.set(SESSION_COOKIE, "esto-no-es-un-token")

    assert client.post("/api/auth/logout").status_code == 200


def test_la_cookie_sale_con_max_age_cero(client, usuario):
    """
    `Max-Age=0` es lo que hace que el navegador la borre, y manda sobre
    `expires` (RFC 6265). Es la parte de la cabecera que de verdad cierra
    la sesión, así que se comprueba aparte.

    Nota de por qué este test mira la cabecera y no el bote de cookies del
    cliente: httpx no da por vencida una cookie cuyo `expires` cae en el
    instante exacto de ahora, que es lo que genera Starlette al borrarla.
    Comprobar el bote sería medir el comportamiento de httpx, no el
    nuestro. La cabecera sí es nuestra.
    """
    client.cookies.set(SESSION_COOKIE, create_session_token(usuario.id))

    set_cookie = client.post("/api/auth/logout").headers.get("set-cookie", "")

    assert "Max-Age=0" in set_cookie
