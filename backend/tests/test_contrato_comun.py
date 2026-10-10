"""
Contrato común de la API (issue #138, B0).

Tres cosas:

1. Los enums nuevos y el estado derivado de una alerta.
2. Los campos de lectura (`*_name`, `floor`) en sites, sensores y alertas.
3. Los filtros comunes (`q`, `organization_id`, `site_id`), y sobre todo
   que **estrechan** lo que deja ver la sesión, nunca lo amplían.
"""

from datetime import datetime, timezone
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
from app.modules.alerts.model import Alert
from app.modules.organizations.model import Organization
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User
from app.shared.dependencies import get_search
from app.shared.enums import AlertState


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


def _montar_cliente(session, nombre, edificio, planta):
    org = Organization(name=nombre)
    session.add(org)
    session.flush()

    site = Site(organization_id=org.id, name=edificio, address=f"Calle de {nombre}")
    session.add(site)
    session.flush()

    sensor = Sensor(
        site_id=site.id,
        external_id=f"SENS-{nombre}",
        name=f"Bombas {nombre}",
        location="Cuarto de máquinas",
        floor=planta,
        unit="bar",
        low_threshold=Decimal("1.000"),
        high_threshold=Decimal("10.000"),
    )
    user = User(
        organization_id=org.id,
        email=f"{nombre}@aquaguard.dev".lower().replace(" ", ""),
        name=f"Usuario de {nombre}",
        password_hash="da-igual-aqui",
        role="client",
    )
    session.add_all([sensor, user])
    session.flush()

    alerta = Alert(
        sensor_id=sensor.id,
        alert_type="LOW_PRESSURE",
        severity="WARNING",
        message=f"Presión baja en {edificio}",
        status="ACTIVE",
    )
    session.add(alerta)
    session.flush()
    return {"org": org, "site": site, "sensor": sensor, "user": user, "alerta": alerta}


@pytest.fixture()
def datos(engine):
    with Session(engine, expire_on_commit=False) as session:
        a = _montar_cliente(session, "Hotel Sol", "Torre Sol", planta=2)
        b = _montar_cliente(session, "Colegio Luna", "Pabellón Luna", planta=-1)
        admin = User(
            email="admin@aquaguard.dev",
            name="Admin",
            password_hash="da-igual-aqui",
            role="admin",
        )
        session.add(admin)
        session.commit()
        return {"a": a, "b": b, "admin": admin}


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


def _ids(cuerpo):
    return {item["id"] for item in cuerpo["items"]}


# ---------------------------------------------------------
# 1. ENUMS Y ESTADO DERIVADO
# ---------------------------------------------------------
def test_estado_de_alerta_activa_sin_reconocer():
    assert AlertState.derive("ACTIVE", None) is AlertState.ACTIVE


def test_estado_de_alerta_reconocida_que_sigue_activa():
    ahora = datetime.now(timezone.utc)
    assert AlertState.derive("ACTIVE", ahora) is AlertState.ACKNOWLEDGED


def test_una_alerta_resuelta_es_resuelta_aunque_se_reconociera():
    ahora = datetime.now(timezone.utc)
    assert AlertState.derive("RESOLVED", ahora) is AlertState.RESOLVED


@pytest.mark.parametrize("q", [None, "", "   "])
def test_q_vacio_es_como_no_enviarlo(q):
    assert get_search(q) is None


def test_q_se_recorta():
    assert get_search("  sol ") == "sol"


def test_el_openapi_publica_los_enums_del_contrato(client):
    schemas = client.get("/api/openapi.json").json()["components"]["schemas"]

    assert schemas["OrganizationStatus"]["enum"] == ["TRIAL", "ACTIVE", "SUSPENDED"]
    assert schemas["SensorHealth"]["enum"] == ["OK", "WARNING", "CRITICAL", "OFFLINE"]
    assert schemas["AlertState"]["enum"] == ["ACTIVE", "ACKNOWLEDGED", "RESOLVED"]
    assert "BuildingType" in schemas


# ---------------------------------------------------------
# 2. CAMPOS DE LECTURA
# ---------------------------------------------------------
def test_el_site_trae_el_nombre_de_su_organizacion(client, datos):
    _entrar(client, datos["a"]["user"])

    item = client.get("/api/sites").json()["items"][0]

    assert item["organization_name"] == "Hotel Sol"


def test_el_sensor_trae_edificio_organizacion_y_planta(client, datos):
    _entrar(client, datos["b"]["user"])

    item = client.get("/api/sensors").json()["items"][0]

    assert item["site_name"] == "Pabellón Luna"
    assert item["organization_id"] == str(datos["b"]["org"].id)
    assert item["organization_name"] == "Colegio Luna"
    assert item["floor"] == -1


def test_el_detalle_del_sensor_trae_los_mismos_campos(client, datos):
    _entrar(client, datos["a"]["user"])
    sensor_id = datos["a"]["sensor"].id

    item = client.get(f"/api/sensors/{sensor_id}").json()

    assert item["site_name"] == "Torre Sol"
    assert item["floor"] == 2


def test_la_alerta_trae_sensor_edificio_organizacion_planta_y_estado(client, datos):
    _entrar(client, datos["a"]["user"])

    item = client.get("/api/alerts").json()["items"][0]

    assert item["sensor_name"] == "Bombas Hotel Sol"
    assert item["site_id"] == str(datos["a"]["site"].id)
    assert item["site_name"] == "Torre Sol"
    assert item["organization_name"] == "Hotel Sol"
    assert item["floor"] == 2
    assert item["state"] == "ACTIVE"


def test_reconocer_una_alerta_la_deja_en_estado_acknowledged(client, datos):
    _entrar(client, datos["a"]["user"])
    alerta_id = datos["a"]["alerta"].id

    item = client.patch(f"/api/alerts/{alerta_id}/acknowledge").json()

    assert item["status"] == "ACTIVE"
    assert item["state"] == "ACKNOWLEDGED"


def test_resolver_una_alerta_la_deja_en_estado_resolved(client, datos):
    _entrar(client, datos["a"]["user"])
    alerta_id = datos["a"]["alerta"].id

    item = client.patch(f"/api/alerts/{alerta_id}/resolve").json()

    assert item["state"] == "RESOLVED"


# ---------------------------------------------------------
# 3. FILTROS COMUNES
# ---------------------------------------------------------
@pytest.mark.parametrize("ruta", ["/api/sites", "/api/sensors", "/api/alerts"])
def test_el_admin_filtra_por_organizacion(client, datos, ruta):
    _entrar(client, datos["admin"])
    org_b = datos["b"]["org"].id

    todo = client.get(ruta).json()
    solo_b = client.get(ruta, params={"organization_id": str(org_b)}).json()

    assert todo["total"] == 2
    assert solo_b["total"] == 1


@pytest.mark.parametrize("ruta", ["/api/sites", "/api/sensors", "/api/alerts"])
def test_un_cliente_no_puede_pedir_los_datos_de_otra_organizacion(client, datos, ruta):
    """El filtro estrecha la sesión: con otra organización sale vacío."""
    _entrar(client, datos["a"]["user"])
    org_b = datos["b"]["org"].id

    cuerpo = client.get(ruta, params={"organization_id": str(org_b)}).json()

    assert cuerpo["total"] == 0
    assert cuerpo["items"] == []


@pytest.mark.parametrize("ruta", ["/api/sensors", "/api/alerts"])
def test_el_admin_filtra_por_edificio(client, datos, ruta):
    _entrar(client, datos["admin"])
    site_a = datos["a"]["site"].id

    cuerpo = client.get(ruta, params={"site_id": str(site_a)}).json()

    assert cuerpo["total"] == 1
    assert cuerpo["items"][0]["site_name"] == "Torre Sol"


@pytest.mark.parametrize(
    ("ruta", "q", "esperado"),
    [
        ("/api/sites", "torre", "a"),  # nombre, sin mayúsculas
        ("/api/sites", "colegio luna", "b"),  # dirección
        ("/api/sensors", "sens-colegio", "b"),  # external_id
        ("/api/sensors", "bombas hotel", "a"),  # nombre
        ("/api/alerts", "pabellón", "b"),  # mensaje
    ],
)
def test_q_busca_sin_distinguir_mayusculas(client, datos, ruta, q, esperado):
    _entrar(client, datos["admin"])

    cuerpo = client.get(ruta, params={"q": q}).json()

    assert cuerpo["total"] == 1
    clave = {"/api/sites": "site", "/api/sensors": "sensor", "/api/alerts": "alerta"}
    assert _ids(cuerpo) == {str(datos[esperado][clave[ruta]].id)}


def test_q_vacio_no_filtra(client, datos):
    _entrar(client, datos["admin"])

    assert client.get("/api/sensors", params={"q": "  "}).json()["total"] == 2


def test_los_comodines_de_like_se_buscan_como_texto(client, datos):
    """`%` no es «cualquier cosa»: nadie se llama así, sale vacío."""
    _entrar(client, datos["admin"])

    assert client.get("/api/sites", params={"q": "%"}).json()["total"] == 0
    assert client.get("/api/sites", params={"q": "_"}).json()["total"] == 0


def test_q_demasiado_largo_da_422(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.get("/api/sites", params={"q": "x" * 101})

    assert respuesta.status_code == 422
