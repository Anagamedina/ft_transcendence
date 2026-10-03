"""
Sites (issue #29, parte A): `GET /api/sites` y `GET /api/sites/{id}`.

Mismo alcance que el resto de la API desde la #27: un admin ve los sites de
todas las organizaciones; un cliente, solo los suyos; un cliente sin
organización, 403. Que sin sesión respondan 401 ya lo comprueba
`test_permisos.py`, que recorre todas las rutas.
"""

from decimal import Decimal
from uuid import uuid4

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
from app.modules.sites.model import Site
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


def _usuario(session, email, role, organization_id):
    user = User(
        organization_id=organization_id,
        email=email,
        name=email.split("@")[0],
        password_hash="da-igual-aqui",
        role=role,
    )
    session.add(user)
    return user


@pytest.fixture()
def datos(engine):
    with Session(engine, expire_on_commit=False) as session:
        a = Organization(name="Cliente A")
        b = Organization(name="Cliente B")
        session.add_all([a, b])
        session.flush()

        # Nombres elegidos para comprobar el orden: Barcelona < Madrid < Valencia.
        madrid = Site(
            organization_id=a.id,
            name="Madrid",
            address="Calle Mayor 4",
            latitude=Decimal("40.416900"),
            longitude=Decimal("-3.703800"),
        )
        barcelona = Site(organization_id=a.id, name="Barcelona")  # sin coordenadas
        valencia = Site(organization_id=b.id, name="Valencia")
        session.add_all([madrid, barcelona, valencia])

        usuarios = {
            "admin": _usuario(session, "admin@aquaguard.dev", "admin", None),
            "cliente_a": _usuario(session, "a@aquaguard.dev", "client", a.id),
            "cliente_sin_org": _usuario(session, "huerfano@aquaguard.dev", "client", None),
        }
        session.commit()
        return {
            "madrid": madrid,
            "barcelona": barcelona,
            "valencia": valencia,
            **usuarios,
        }


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


def _nombres(respuesta):
    return [s["name"] for s in respuesta.json()["items"]]


# ---------------------------------------------------------
# GET /api/sites
# ---------------------------------------------------------
def test_el_admin_ve_los_sites_de_todas_las_organizaciones(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.get("/api/sites")

    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 3
    # Ordenados por nombre.
    assert _nombres(respuesta) == ["Barcelona", "Madrid", "Valencia"]


def test_un_cliente_solo_ve_los_suyos(client, datos):
    _entrar(client, datos["cliente_a"])

    respuesta = client.get("/api/sites")

    assert respuesta.json()["total"] == 2
    assert _nombres(respuesta) == ["Barcelona", "Madrid"]


def test_un_cliente_sin_organizacion_no_ve_nada(client, datos):
    _entrar(client, datos["cliente_sin_org"])

    assert client.get("/api/sites").status_code == 403


def test_la_lista_va_paginada(client, datos):
    _entrar(client, datos["admin"])

    primera = client.get("/api/sites", params={"page": 1, "page_size": 2}).json()
    segunda = client.get("/api/sites", params={"page": 2, "page_size": 2}).json()

    assert primera["total"] == 3
    assert primera["pages"] == 2
    assert [s["name"] for s in primera["items"]] == ["Barcelona", "Madrid"]
    assert [s["name"] for s in segunda["items"]] == ["Valencia"]


# ---------------------------------------------------------
# GET /api/sites/{id}
# ---------------------------------------------------------
def test_un_cliente_ve_su_site_con_las_coordenadas_como_numeros(client, datos):
    """La tabla las guarda como Decimal; el mapa las necesita como número."""
    _entrar(client, datos["cliente_a"])

    respuesta = client.get(f"/api/sites/{datos['madrid'].id}")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["name"] == "Madrid"
    assert cuerpo["address"] == "Calle Mayor 4"
    assert cuerpo["latitude"] == pytest.approx(40.4169)
    assert cuerpo["longitude"] == pytest.approx(-3.7038)
    assert isinstance(cuerpo["latitude"], float)


def test_un_site_sin_coordenadas_las_devuelve_nulas(client, datos):
    _entrar(client, datos["cliente_a"])

    cuerpo = client.get(f"/api/sites/{datos['barcelona'].id}").json()

    assert cuerpo["latitude"] is None
    assert cuerpo["longitude"] is None


def test_un_cliente_no_ve_un_site_ajeno(client, datos):
    """404 y no 403: no se confirma que el site exista."""
    _entrar(client, datos["cliente_a"])

    respuesta = client.get(f"/api/sites/{datos['valencia'].id}")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "SITE_NOT_FOUND"


def test_el_admin_ve_un_site_de_cualquier_organizacion(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.get(f"/api/sites/{datos['valencia'].id}")

    assert respuesta.status_code == 200
    assert respuesta.json()["name"] == "Valencia"


def test_un_site_que_no_existe_da_404(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.get(f"/api/sites/{uuid4()}")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "SITE_NOT_FOUND"
