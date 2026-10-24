"""
«Hazte cliente» (B14, issue #150).

Cubre el catálogo de planes, quién puede suscribirse, el plan y el precio
que salen de los edificios y sensores contratados, el paso de TRIAL a
ACTIVE con el periodo, los datos fiscales y la domiciliación, que el IBAN
nunca se guarda entero y los límites (1 edificio en prueba, lo contratado
como cliente).
"""

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.app_config import app_settings
from app.core.database import Base, get_db
from app.core.exceptions import DomainValidationError
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.organizations.model import Organization
from app.modules.sites.model import Site
from app.modules.sensors.model import Sensor
from app.modules.subscriptions.plans import (
    TRIAL_MAX_SITES,
    max_sensors_for,
    max_sites_for,
    monthly_price,
    plan_for,
)
from app.modules.subscriptions.service import (
    check_postal_code,
    mask_iban,
    normalize_tax_id,
)
from app.modules.users.model import User

IBAN = "ES91 2100 0418 4502 0005 1332"
URL = "/api/me/organization/subscribe"


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
    """Luna en prueba, Nube con la prueba caducada y Sol ya cliente."""
    ahora = datetime.now(timezone.utc)
    with Session(engine, expire_on_commit=False) as s:
        luna = Organization(
            name="Colegio Luna", status="TRIAL", trial_ends_at=ahora + timedelta(days=3),
            contact_email="antes@luna.dev",
        )
        nube = Organization(
            name="Gimnasio Nube", status="TRIAL", trial_ends_at=ahora - timedelta(days=1)
        )
        sol = Organization(name="Hotel Sol", status="ACTIVE")
        s.add_all([luna, nube, sol])
        s.flush()
        usuarios = {
            "luna": User(organization_id=luna.id, email="c@luna.dev", name="Luna",
                         password_hash="x", role="client"),
            "nube": User(organization_id=nube.id, email="c@nube.dev", name="Nube",
                         password_hash="x", role="client"),
            "sol": User(organization_id=sol.id, email="c@sol.dev", name="Sol",
                        password_hash="x", role="client"),
            "admin": User(email="admin@aquaguard.dev", name="Admin",
                          password_hash="x", role="admin"),
        }
        s.add_all(usuarios.values())
        s.commit()
        return {"luna": luna, "nube": nube, "sol": sol, **{f"u_{k}": v for k, v in usuarios.items()}}


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


def _cuerpo(**cambios):
    """Un edificio con 8 sensores: plan Básico, 29 + 8 × 10 = 109 € al mes."""
    cuerpo = {
        "sites": 1,
        "sensors": 8,
        "billing_period": "YEARLY",
        "legal_name": "Colegio Luna S.L.",
        "tax_id": "b-1234 5678",
        "billing_address": "Carrer de la Lluna 1",
        "postal_code": "08001",
        "city": "Barcelona",
        "billing_email": "facturas@luna.dev",
        "iban": IBAN,
        "accept_terms": True,
        "accept_sepa": True,
    }
    cuerpo.update(cambios)
    return cuerpo


def _codigo(respuesta):
    return respuesta.json()["error"]["code"]


def _edificios(engine, organizacion, cuantos, sensores_por_edificio=0):
    with Session(engine) as s:
        for n in range(cuantos):
            site = Site(organization_id=organizacion.id, name=f"Edificio {n}")
            s.add(site)
            s.flush()
            s.add_all(
                Sensor(site_id=site.id, external_id=f"S-{n}-{m}", name=f"Sensor {m}",
                       floor=0, unit="bar", low_threshold=1, high_threshold=9)
                for m in range(sensores_por_edificio)
            )
        s.commit()


# ---------------------------------------------------------
# PLANES Y PRECIO
# ---------------------------------------------------------
def test_los_planes_se_ven_sin_sesion(client):
    respuesta = client.get("/api/plans")

    assert respuesta.status_code == 200
    planes = respuesta.json()
    assert [p["id"] for p in planes] == ["BASIC", "PRO", "ENTERPRISE"]
    assert (planes[0]["max_sites"], planes[0]["max_sensors"]) == (1, 10)
    assert planes[2]["max_sensors"] is None
    assert (planes[0]["sensor_price_eur"], planes[0]["yearly_months"]) == (10, 10)


@pytest.mark.parametrize(
    ("edificios", "sensores", "plan", "precio"),
    [
        # Los ejemplos de la tabla de precios
        (1, 5, "BASIC", 79),
        (1, 8, "BASIC", 109),
        (2, 12, "PRO", 199),
        (3, 18, "PRO", 259),
        (10, 80, "ENTERPRISE", 999),
        # Un edificio con más de 10 sensores ya no cabe en el Básico
        (1, 11, "PRO", 189),
        # Ni 6 edificios en el Profesional
        (6, 12, "ENTERPRISE", 319),
    ],
)
def test_plan_y_precio_salen_de_edificios_y_sensores(edificios, sensores, plan, precio):
    elegido = plan_for(edificios, sensores)
    assert elegido.id.value == plan
    assert monthly_price(elegido, sensores) == precio


# ---------------------------------------------------------
# PERMISOS
# ---------------------------------------------------------
def test_sin_sesion_da_401(client, datos):
    assert client.post(URL, json=_cuerpo()).status_code == 401


def test_un_admin_no_puede_suscribirse(client, datos):
    _entrar(client, datos["u_admin"])
    assert client.post(URL, json=_cuerpo()).status_code == 403


def test_un_cliente_ya_activo_recibe_409(client, datos):
    _entrar(client, datos["u_sol"])
    respuesta = client.post(URL, json=_cuerpo())

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "ORGANIZATION_NOT_IN_TRIAL"


# ---------------------------------------------------------
# SUSCRIPCIÓN
# ---------------------------------------------------------
def test_el_cliente_en_prueba_pasa_a_activo(client, datos, engine):
    _entrar(client, datos["u_luna"])
    respuesta = client.post(URL, json=_cuerpo())

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["status"] == "ACTIVE"
    assert (cuerpo["plan"], cuerpo["plan_name"]) == ("BASIC", "Básico")
    assert (cuerpo["contracted_sites"], cuerpo["contracted_sensors"]) == (1, 8)
    # Anual: diez meses de 109 €
    assert (cuerpo["monthly_price_eur"], cuerpo["billed_price_eur"]) == (109, 1090)
    assert cuerpo["billing_period"] == "YEARLY"
    assert cuerpo["tax_id"] == "B12345678"
    assert cuerpo["postal_code"] == "08001"
    assert cuerpo["sepa_accepted_at"] is not None
    assert cuerpo["iban_masked"] == "ES** **** **** **** **** 1332"
    assert "iban" not in cuerpo
    # El contacto que no llega se queda como estaba
    assert cuerpo["contact_email"] == "antes@luna.dev"

    with Session(engine) as s:
        luna = s.get(Organization, datos["luna"].id)
        assert luna.status == "ACTIVE"
        assert luna.trial_ends_at is None
        assert luna.subscribed_at is not None
        assert luna.plan == "BASIC"
        assert (luna.contracted_sites, luna.contracted_sensors) == (1, 8)
        assert luna.monthly_price_eur == 109
        assert luna.billing_period == "YEARLY"
        assert luna.billing_address == "Carrer de la Lluna 1"
        assert luna.postal_code == "08001"
        assert luna.city == "Barcelona"
        assert luna.sepa_accepted_at is not None
        usuario = s.get(User, datos["u_luna"].id)
        assert usuario.terms_version == app_settings.TERMS_VERSION
        assert usuario.terms_accepted_at is not None


def test_el_plan_no_se_puede_elegir_a_mano(client, datos):
    """El plan lo calcula la API: si llega, es un campo que no existe."""
    _entrar(client, datos["u_luna"])
    respuesta = client.post(URL, json=_cuerpo(plan="BASIC", sensors=40))

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "VALIDATION_ERROR"


def test_el_iban_entero_no_se_guarda_en_ninguna_columna(client, datos, engine):
    _entrar(client, datos["u_luna"])
    client.post(URL, json=_cuerpo())

    with Session(engine) as s:
        luna = s.get(Organization, datos["luna"].id)
        valores = [str(getattr(luna, c.key)) for c in Organization.__table__.columns]
    assert not any("21000418" in v for v in valores)


def test_una_prueba_caducada_tambien_puede_suscribirse(client, datos):
    _entrar(client, datos["u_nube"])
    respuesta = client.post(
        URL, json=_cuerpo(sites=3, sensors=18, billing_period="MONTHLY")
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert (cuerpo["plan"], cuerpo["billing_period"]) == ("PRO", "MONTHLY")
    assert cuerpo["billed_price_eur"] == 259


def test_el_admin_ve_lo_contratado_en_la_ficha(client, datos):
    _entrar(client, datos["u_luna"])
    client.post(URL, json=_cuerpo())

    _entrar(client, datos["u_admin"])
    ficha = client.get(f"/api/organizations/{datos['luna'].id}").json()
    assert ficha["plan"] == "BASIC"
    assert ficha["billing_period"] == "YEARLY"
    assert (ficha["contracted_sites"], ficha["contracted_sensors"]) == (1, 8)
    assert ficha["monthly_price_eur"] == 109
    assert ficha["postal_code"] == "08001"
    assert ficha["iban_masked"] == "ES** **** **** **** **** 1332"
    assert ficha["sepa_accepted_at"] is not None


# ---------------------------------------------------------
# VALIDACIÓN
# ---------------------------------------------------------
@pytest.mark.parametrize(
    ("cambios", "codigo"),
    [
        ({"accept_terms": False}, "TERMS_NOT_ACCEPTED"),
        ({"accept_sepa": False}, "SEPA_NOT_ACCEPTED"),
        ({"sites": 3, "sensors": 2}, "SENSORS_BELOW_SITES"),
        ({"tax_id": "B1"}, "INVALID_TAX_ID"),
        ({"postal_code": "8001"}, "INVALID_POSTAL_CODE"),
        ({"postal_code": "08O01"}, "INVALID_POSTAL_CODE"),
        ({"iban": "ES00 2100 0418 4502 0005 1332"}, "INVALID_IBAN"),
        ({"iban": "1234"}, "INVALID_IBAN"),
        ({"sites": 0}, "VALIDATION_ERROR"),
        ({"sensors": 0}, "VALIDATION_ERROR"),
        ({"sites": 101}, "VALIDATION_ERROR"),
        ({"sensors": 1001}, "VALIDATION_ERROR"),
        ({"sensors": -5}, "VALIDATION_ERROR"),
        ({"billing_period": "SEMANAL"}, "VALIDATION_ERROR"),
        ({"iban": None}, "VALIDATION_ERROR"),
        ({"city": "   "}, "VALIDATION_ERROR"),
        ({"billing_email": "no-es-un-email"}, "VALIDATION_ERROR"),
    ],
)
def test_datos_incorrectos_dan_422_y_no_cambian_nada(client, datos, engine, cambios, codigo):
    _entrar(client, datos["u_luna"])
    respuesta = client.post(URL, json=_cuerpo(**cambios))

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == codigo
    with Session(engine) as s:
        assert s.get(Organization, datos["luna"].id).status == "TRIAL"


@pytest.mark.parametrize(
    "campo",
    ["sites", "sensors", "legal_name", "billing_period", "postal_code", "city",
     "iban", "accept_sepa"],
)
def test_faltan_datos_obligatorios(client, datos, campo):
    _entrar(client, datos["u_luna"])
    cuerpo = _cuerpo()
    del cuerpo[campo]

    assert client.post(URL, json=cuerpo).status_code == 422


@pytest.mark.parametrize(
    ("cambios", "campo"),
    [({"sites": 1, "sensors": 8}, "sites"), ({"sites": 2, "sensors": 5}, "sensors")],
)
def test_no_se_contrata_menos_de_lo_que_ya_tiene(client, datos, engine, cambios, campo):
    # Edificios de antes del límite de la prueba: 2, con 3 sensores cada uno
    _edificios(engine, datos["luna"], 2, sensores_por_edificio=3)
    _entrar(client, datos["u_luna"])

    respuesta = client.post(URL, json=_cuerpo(**cambios))

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "CONTRACT_BELOW_CURRENT"
    assert respuesta.json()["error"]["details"][0]["field"] == campo
    with Session(engine) as s:
        assert s.get(Organization, datos["luna"].id).status == "TRIAL"
    # Contratando al menos lo que tiene, sí
    assert client.post(URL, json=_cuerpo(sites=2, sensors=6)).status_code == 200


def test_mask_iban_y_normalize_tax_id():
    assert mask_iban("de89370400440532013000") == "DE** **** **** **** **30 00"
    assert normalize_tax_id(" x-1234567.l ") == "X1234567L"
    assert check_postal_code(" 08002 ") == "08002"
    with pytest.raises(DomainValidationError):
        mask_iban("ES91 2100 0418 4502 0005 1333")


# ---------------------------------------------------------
# LÍMITES: EDIFICIOS Y SENSORES
# ---------------------------------------------------------
def _alta_edificio(client, organizacion, nombre="Nuevo"):
    return client.post(
        "/api/sites", json={"organization_id": str(organizacion.id), "name": nombre}
    )


def _alta_sensor(client, site_id, external_id):
    return client.post("/api/sensors", json={
        "site_id": str(site_id), "external_id": external_id, "name": external_id,
        "floor": 0, "sensor_type": "PRESSURE", "unit": "bar",
        "min_pressure": 1, "max_pressure": 9,
    })


def test_en_prueba_solo_cabe_un_edificio(client, datos):
    _entrar(client, datos["u_admin"])
    assert _alta_edificio(client, datos["luna"], "Primero").status_code == 201

    respuesta = _alta_edificio(client, datos["luna"], "Segundo")

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "SITE_LIMIT_REACHED"
    error = respuesta.json()["error"]
    assert error["details"][0]["max_sites"] == TRIAL_MAX_SITES
    assert "en prueba" in error["message"]


def test_como_cliente_caben_los_edificios_contratados(client, datos):
    _entrar(client, datos["u_admin"])
    _alta_edificio(client, datos["luna"], "Primero")
    _entrar(client, datos["u_luna"])
    assert client.post(URL, json=_cuerpo(sites=3, sensors=18)).status_code == 200

    _entrar(client, datos["u_admin"])
    assert _alta_edificio(client, datos["luna"], "Segundo").status_code == 201
    assert _alta_edificio(client, datos["luna"], "Tercero").status_code == 201
    respuesta = _alta_edificio(client, datos["luna"], "Cuarto")

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "SITE_LIMIT_REACHED"
    assert "contratados" in respuesta.json()["error"]["message"]


def test_como_cliente_caben_los_sensores_contratados(client, datos):
    _entrar(client, datos["u_admin"])
    site_id = _alta_edificio(client, datos["luna"]).json()["id"]
    _entrar(client, datos["u_luna"])
    assert client.post(URL, json=_cuerpo(sites=1, sensors=2)).status_code == 200

    _entrar(client, datos["u_admin"])
    assert _alta_sensor(client, site_id, "S-1").status_code == 201
    assert _alta_sensor(client, site_id, "S-2").status_code == 201
    respuesta = _alta_sensor(client, site_id, "S-3")

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "SENSOR_LIMIT_REACHED"
    assert respuesta.json()["error"]["details"][0]["max_sensors"] == 2


def test_un_cliente_activo_sin_contrato_no_tiene_limite(client, datos, engine):
    _edificios(engine, datos["sol"], 5, sensores_por_edificio=2)
    _entrar(client, datos["u_admin"])

    respuesta = _alta_edificio(client, datos["sol"])
    assert respuesta.status_code == 201
    assert _alta_sensor(client, respuesta.json()["id"], "S-extra").status_code == 201


def test_max_sites_y_max_sensors_for():
    prueba = Organization(name="P", status="TRIAL")
    contrato = Organization(name="C", status="ACTIVE", contracted_sites=3,
                            contracted_sensors=18)
    antiguo = Organization(name="A", status="ACTIVE")

    assert (max_sites_for(prueba), max_sensors_for(prueba)) == (1, None)
    assert (max_sites_for(contrato), max_sensors_for(contrato)) == (3, 18)
    assert (max_sites_for(antiguo), max_sensors_for(antiguo)) == (None, None)
