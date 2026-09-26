"""
Resolución de la sesión: `get_current_user` (issue #26).

Se prueba a través de una aplicación FastAPI mínima montada aquí, con un
único endpoint que depende de `CurrentUser`. Así se ejercita el camino
completo —cookie, firma, consulta— sin esperar a que existan las rutas de
auth, que son el paso siguiente de la issue.
"""

from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.database import Base, get_db
from app.core.exceptions import register_exception_handlers
from app.core.security import SESSION_COOKIE, create_session_token
from app.modules.organizations.model import Organization
from app.modules.users.model import User
from app.shared.dependencies import CurrentUser


def _manipular(token: str) -> str:
    """
    Cambia el contenido del token dejando la firma intacta.

    Es lo que intentaría alguien de verdad: tocar el id de usuario que va
    dentro. Y es más fiable que cambiar el último carácter — en base64 el
    último grupo lleva bits de sobra, así que varios caracteres distintos
    decodifican a los mismos bytes y la firma seguiría cuadrando.
    """
    payload, resto = token.split(".", 1)
    alterado = payload[:-1] + ("A" if payload[-1] != "A" else "B")
    return f"{alterado}.{resto}"


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

        # OJO: el rol va en MAYÚSCULAS porque la tabla tiene
        # CheckConstraint("role IN ('ADMIN', 'CLIENT')"), y sqlite también
        # lo aplica. El contrato de la API los declara en minúsculas
        # ("admin"), así que este desajuste sigue pendiente de acordar con
        # Daruny. Aquí no molesta: get_current_user no toca el rol.
        user = User(
            organization_id=organization.id,
            email="ana@aquaguard.dev",
            password_hash="da-igual-aqui",
            role="ADMIN",
        )
        session.add(user)
        session.commit()
        return user


@pytest.fixture()
def client(engine):
    """Aplicación mínima con un endpoint protegido."""

    def _get_db():
        db = Session(engine, expire_on_commit=False)
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/protegido")
    def protegido(user: CurrentUser):
        return {"id": str(user.id), "email": user.email}

    app.dependency_overrides[get_db] = _get_db
    return TestClient(app)


def test_con_sesion_valida_devuelve_el_usuario(client, usuario):
    client.cookies.set(SESSION_COOKIE, create_session_token(usuario.id))

    respuesta = client.get("/protegido")

    assert respuesta.status_code == 200
    assert respuesta.json()["email"] == "ana@aquaguard.dev"


def test_sin_cookie_da_401(client):
    respuesta = client.get("/protegido")

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "UNAUTHORIZED"


def test_con_cookie_manipulada_da_401(client, usuario):
    client.cookies.set(SESSION_COOKIE, _manipular(create_session_token(usuario.id)))

    respuesta = client.get("/protegido")

    assert respuesta.status_code == 401


def test_con_basura_en_la_cookie_da_401(client):
    client.cookies.set(SESSION_COOKIE, "esto-no-es-un-token")

    respuesta = client.get("/protegido")

    assert respuesta.status_code == 401


def test_una_sesion_de_un_usuario_que_ya_no_existe_da_401(client):
    """
    Firma buena, usuario inexistente. Pasa si se borra la cuenta con la
    sesión abierta, y tiene que cortar igual que una firma mala.
    """
    client.cookies.set(SESSION_COOKIE, create_session_token(uuid4()))

    respuesta = client.get("/protegido")

    assert respuesta.status_code == 401


def test_no_dice_por_que_falla_la_sesion(client, usuario):
    """
    Los tres motivos —firma mala, caducada, usuario que no está— dan el
    mismo mensaje. Distinguirlos le diría a quien lo intenta hasta dónde
    ha llegado.
    """
    client.cookies.set(SESSION_COOKIE, _manipular(create_session_token(usuario.id)))
    por_firma = client.get("/protegido").json()["error"]["message"]

    client.cookies.set(SESSION_COOKIE, create_session_token(uuid4()))
    por_usuario = client.get("/protegido").json()["error"]["message"]

    assert por_firma == por_usuario


def test_lee_el_usuario_de_la_base_en_cada_peticion(client, usuario, engine):
    """
    Lo que hace que un cambio de rol tenga efecto en la siguiente petición
    y no cuando el usuario vuelva a entrar. Si el usuario saliera de la
    cookie, este test fallaría.
    """
    client.cookies.set(SESSION_COOKIE, create_session_token(usuario.id))
    assert client.get("/protegido").status_code == 200

    with Session(engine) as session:
        session.query(User).filter_by(id=usuario.id).update(
            {"email": "otro@aquaguard.dev"}
        )
        session.commit()

    assert client.get("/protegido").json()["email"] == "otro@aquaguard.dev"
