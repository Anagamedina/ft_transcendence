"""
Permisos y aislamiento por organización (issue #27).

Tres preguntas, en este orden:

1. **¿Quién eres?** Sin sesión, toda ruta privada responde 401. El test
   recorre la lista real de rutas de la app: si alguien añade una ruta
   nueva sin proteger, falla sin que haya que acordarse de escribirle un
   test.
2. **¿Puedes hacer esto?** Un cliente en una ruta de admin, 403.
3. **¿Qué puedes ver?** Decidido por Ana el 28-09-2026: un admin ve todas
   las organizaciones, tenga o no organización propia; un cliente solo la
   suya; un cliente sin organización, 403 (`get_org_scope`).
"""

from datetime import datetime, timezone
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
from app.modules.alerts.model import Alert
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

# Las únicas rutas que se pueden llamar sin sesión, y por qué.
RUTAS_PUBLICAS = {
    ("GET", "/api/health"),  # liveness de Docker
    ("GET", "/api/health/db"),  # readiness de Docker
    ("POST", "/api/auth/login"),  # es como se consigue la sesión
    ("POST", "/api/auth/logout"),  # salir tiene que funcionar siempre
}


@pytest.fixture()
def engine():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return engine


def _organizacion(session, nombre):
    org = Organization(name=nombre)
    session.add(org)
    session.flush()

    site = Site(organization_id=org.id, name=f"Sede de {nombre}")
    session.add(site)
    session.flush()

    sensor = Sensor(
        site_id=site.id,
        external_id=f"SENS-{nombre}",
        name=f"Sensor de {nombre}",
        unit="bar",
    )
    session.add(sensor)
    session.flush()

    alerta = Alert(
        sensor_id=sensor.id,
        alert_type="LOW_PRESSURE",
        severity="WARNING",
        message=f"Presión baja en {nombre}",
        status="ACTIVE",
    )
    lectura = Reading(
        sensor_id=sensor.id,
        value=3,
        unit="bar",
        recorded_at=datetime(2026, 9, 28, 9, 0, tzinfo=timezone.utc),
    )
    session.add_all([alerta, lectura])
    session.flush()
    return {"org": org, "sensor": sensor, "alerta": alerta}


def _usuario(session, email, role, organization_id):
    user = User(
        organization_id=organization_id,
        email=email,
        name=email.split("@")[0],
        password_hash="da-igual-aqui",
        role=role,
    )
    session.add(user)
    session.flush()
    return user


@pytest.fixture()
def datos(engine):
    with Session(engine, expire_on_commit=False) as session:
        a = _organizacion(session, "ClienteA")
        b = _organizacion(session, "ClienteB")
        usuarios = {
            "admin_global": _usuario(session, "global@aquaguard.dev", "admin", None),
            "admin_de_a": _usuario(session, "admin-a@aquaguard.dev", "admin", a["org"].id),
            "cliente_a": _usuario(session, "cliente-a@aquaguard.dev", "client", a["org"].id),
            "cliente_sin_org": _usuario(session, "huerfano@aquaguard.dev", "client", None),
        }
        session.commit()
        return {"a": a, "b": b, **usuarios}


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


def _ids_de_alertas(respuesta):
    return {item["id"] for item in respuesta.json()["items"]}


# ---------------------------------------------------------
# 1 · Sin sesión → 401
# ---------------------------------------------------------
def _rutas_privadas():
    rutas = []
    for ruta in app.routes:
        metodos = getattr(ruta, "methods", None) or set()
        if not ruta.path.startswith("/api") or ruta.path.startswith(
            ("/api/docs", "/api/redoc", "/api/openapi")
        ):
            continue
        for metodo in sorted(metodos - {"HEAD", "OPTIONS"}):
            if (metodo, ruta.path) not in RUTAS_PUBLICAS:
                rutas.append((metodo, ruta.path))
    return rutas


def test_hay_rutas_privadas_que_comprobar():
    """Si la lista saliera vacía, el test de abajo pasaría sin probar nada."""
    assert len(_rutas_privadas()) >= 5


@pytest.mark.parametrize(("metodo", "ruta"), _rutas_privadas())
def test_toda_ruta_privada_sin_sesion_da_401(client, metodo, ruta):
    # Los ids de la ruta dan igual: la sesión se comprueba antes de buscar nada.
    url = ruta.replace("{sensor_id}", str(uuid4())).replace("{alert_id}", str(uuid4()))

    respuesta = client.request(metodo, url, json={})

    assert respuesta.status_code == 401, f"{metodo} {ruta} no pide sesión"


# ---------------------------------------------------------
# 2 · Rol
# ---------------------------------------------------------
def test_un_cliente_no_puede_dar_de_alta_cuentas(client, datos):
    _entrar(client, datos["cliente_a"])

    respuesta = client.post(
        "/api/auth/register",
        json={
            "email": "nuevo@aquaguard.dev",
            "name": "Nuevo",
            "password": "una-contrasena-larga",
            "organization_id": str(datos["a"]["org"].id),
        },
    )

    assert respuesta.status_code == 403
    assert respuesta.json()["error"]["code"] == "FORBIDDEN"


# ---------------------------------------------------------
# 3 · Qué ve cada uno
# ---------------------------------------------------------
@pytest.mark.parametrize("quien", ["admin_global", "admin_de_a"])
def test_un_admin_ve_las_alertas_de_todas_las_organizaciones(client, datos, quien):
    """También el admin con organización: gestiona las de todos los clientes."""
    _entrar(client, datos[quien])

    respuesta = client.get("/api/alerts")

    assert respuesta.status_code == 200
    assert _ids_de_alertas(respuesta) == {
        str(datos["a"]["alerta"].id),
        str(datos["b"]["alerta"].id),
    }


def test_un_cliente_solo_ve_las_de_su_organizacion(client, datos):
    _entrar(client, datos["cliente_a"])

    respuesta = client.get("/api/alerts")

    assert _ids_de_alertas(respuesta) == {str(datos["a"]["alerta"].id)}


def test_un_admin_puede_resolver_una_alerta_de_otra_organizacion(client, datos):
    _entrar(client, datos["admin_global"])

    respuesta = client.patch(f"/api/alerts/{datos['b']['alerta'].id}/resolve")

    assert respuesta.status_code == 200
    assert respuesta.json()["status"] == "RESOLVED"


def test_un_cliente_no_puede_resolver_una_alerta_ajena(client, datos):
    """404 y no 403: no se confirma que la alerta exista."""
    _entrar(client, datos["cliente_a"])

    respuesta = client.patch(f"/api/alerts/{datos['b']['alerta'].id}/resolve")

    assert respuesta.status_code == 404


def test_un_admin_ve_el_historico_de_cualquier_sensor(client, datos):
    _entrar(client, datos["admin_global"])

    respuesta = client.get(f"/api/sensors/{datos['b']['sensor'].id}/readings")

    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 1


def test_un_cliente_no_ve_el_historico_de_un_sensor_ajeno(client, datos):
    _entrar(client, datos["cliente_a"])

    respuesta = client.get(f"/api/sensors/{datos['b']['sensor'].id}/readings")

    assert respuesta.status_code == 404


@pytest.mark.parametrize(
    "url",
    ["/api/alerts", "/api/sensors/{sensor}/readings"],
)
def test_un_cliente_sin_organizacion_no_ve_nada(client, datos, url):
    """
    El caso peligroso: `None` significa «todas» para un admin. Si se colara
    para un cliente, vería los datos de todos. `get_org_scope` lo corta.
    """
    _entrar(client, datos["cliente_sin_org"])

    respuesta = client.get(url.format(sensor=datos["a"]["sensor"].id))

    assert respuesta.status_code == 403


# ---------------------------------------------------------
# Registro: a qué organización va el cliente
# ---------------------------------------------------------
def _registrar(client, **cambios):
    cuerpo = {
        "email": "nuevo@aquaguard.dev",
        "name": "Nuevo",
        "password": "una-contrasena-larga",
        **cambios,
    }
    return client.post("/api/auth/register", json=cuerpo)


def test_el_admin_global_da_de_alta_un_cliente_en_una_organizacion(client, datos):
    """Antes de la #27 este cliente se creaba sin organización."""
    _entrar(client, datos["admin_global"])

    respuesta = _registrar(client, organization_id=str(datos["b"]["org"].id))

    assert respuesta.status_code == 201
    assert respuesta.json()["user"]["organization_id"] == str(datos["b"]["org"].id)
    assert respuesta.json()["user"]["role"] == "client"


def test_registrar_sin_organizacion_da_422(client, datos):
    _entrar(client, datos["admin_global"])

    respuesta = _registrar(client)

    assert respuesta.status_code == 422


def test_registrar_en_una_organizacion_que_no_existe_da_404(client, datos, engine):
    _entrar(client, datos["admin_global"])

    respuesta = _registrar(client, organization_id=str(uuid4()))

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "ORGANIZATION_NOT_FOUND"
    with Session(engine) as session:
        assert session.query(User).filter_by(email="nuevo@aquaguard.dev").count() == 0
