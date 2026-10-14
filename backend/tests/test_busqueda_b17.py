"""
Búsqueda global del panel (B17, issue #150).

Lo que más importa: encuentra clientes, edificios y sensores por nombre,
y un cliente nunca ve nada de otra organización.
"""

from decimal import Decimal

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
from app.modules.sensors.model import Sensor
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


@pytest.fixture()
def datos(engine):
    """
    Hotel Diagonal: edificio «Torre Diagonal» con el sensor «Bomba Diagonal».
    Residencia Mar: edificio «Anexo» en la Diagonal, con «Montante Diagonal».
    """
    with Session(engine, expire_on_commit=False) as s:
        hotel = Organization(name="Hotel Diagonal", city="Barcelona")
        residencia = Organization(name="Residencia Mar")
        s.add_all([hotel, residencia])
        s.flush()
        torre = Site(organization_id=hotel.id, name="Torre Diagonal")
        anexo = Site(organization_id=residencia.id, name="Anexo", address="Av. Diagonal 3")
        s.add_all([torre, anexo])
        s.flush()
        s.add_all(
            [
                Sensor(site_id=torre.id, external_id="S-1", name="Bomba Diagonal",
                       unit="bar", low_threshold=Decimal("1"), high_threshold=Decimal("9")),
                Sensor(site_id=anexo.id, external_id="S-2", name="Montante Diagonal",
                       unit="bar", low_threshold=Decimal("1"), high_threshold=Decimal("9")),
            ]
        )
        cliente = User(organization_id=hotel.id, email="c@hotel.dev", name="Cliente",
                       password_hash="x", role="client")
        admin = User(email="admin@aquaguard.dev", name="Admin", password_hash="x",
                     role="admin")
        s.add_all([cliente, admin])
        s.commit()
        return {"hotel": hotel, "residencia": residencia, "cliente": cliente, "admin": admin}


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


def _nombres(grupo):
    return [item["name"] for item in grupo["items"]]


def test_sin_sesion_da_401(client, datos):
    assert client.get("/api/search?q=diag").status_code == 401


def test_el_admin_encuentra_clientes_edificios_y_sensores(client, datos):
    _entrar(client, datos["admin"])
    cuerpo = client.get("/api/search?q=DIAG").json()

    assert cuerpo["q"] == "DIAG"
    assert _nombres(cuerpo["organizations"]) == ["Hotel Diagonal"]
    # «Anexo» sale por la dirección
    assert _nombres(cuerpo["sites"]) == ["Anexo", "Torre Diagonal"]
    assert _nombres(cuerpo["sensors"]) == ["Bomba Diagonal", "Montante Diagonal"]
    sensor = cuerpo["sensors"]["items"][0]
    assert sensor["site_name"] == "Torre Diagonal"
    assert sensor["organization_name"] == "Hotel Diagonal"


def test_un_cliente_solo_ve_lo_suyo_y_ninguna_organizacion(client, datos):
    _entrar(client, datos["cliente"])
    cuerpo = client.get("/api/search?q=diag").json()

    assert cuerpo["organizations"] == {"items": [], "total": 0}
    assert _nombres(cuerpo["sites"]) == ["Torre Diagonal"]
    assert _nombres(cuerpo["sensors"]) == ["Bomba Diagonal"]
    assert cuerpo["sensors"]["total"] == 1


def test_limit_recorta_los_resultados_pero_no_el_total(client, datos):
    _entrar(client, datos["admin"])
    cuerpo = client.get("/api/search?q=diag&limit=1").json()

    assert len(cuerpo["sensors"]["items"]) == 1
    assert cuerpo["sensors"]["total"] == 2


def test_los_comodines_de_like_se_buscan_como_texto(client, datos):
    _entrar(client, datos["admin"])
    cuerpo = client.get("/api/search", params={"q": "%%"}).json()

    assert cuerpo["sites"]["total"] == 0
    assert cuerpo["sensors"]["total"] == 0


@pytest.mark.parametrize("q", ["d", "   x   ", ""])
def test_q_demasiado_corto_da_422(client, datos, q):
    _entrar(client, datos["admin"])
    respuesta = client.get("/api/search", params={"q": q})

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "QUERY_TOO_SHORT"


def test_sin_q_da_422(client, datos):
    _entrar(client, datos["admin"])
    assert client.get("/api/search").status_code == 422
