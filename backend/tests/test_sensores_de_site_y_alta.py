"""
Issue #29, partes B y C.

- B · `GET /api/sites/{id}/sensors`: los sensores de un site, con el mismo
  formato que `GET /api/sensors`.
- C · `POST /api/sensors` y `PATCH /api/sensors/{id}`, solo admin.

Decisiones de Ana del 03-10-2026: se pueden crear sensores `FLOW`, y de un
sensor se editan nombre, ubicación y umbrales (no el site, el tipo ni el
`external_id`).
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

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
from app.modules.readings.model import Reading
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
        hotel = Site(organization_id=a.id, name="Hotel")
        vacio = Site(organization_id=a.id, name="Almacén")
        deposito = Site(organization_id=b.id, name="Depósito")
        session.add_all([hotel, vacio, deposito])
        session.flush()

        entrada = Sensor(
            site_id=hotel.id,
            external_id="SENS-001",
            name="Entrada",
            unit="bar",
            low_threshold=Decimal("1.500"),
            high_threshold=Decimal("6.000"),
        )
        session.add(entrada)
        session.flush()
        ahora = datetime.now(timezone.utc)
        session.add(
            Reading(
                sensor_id=entrada.id,
                value=Decimal("3.5"),
                unit="bar",
                recorded_at=ahora - timedelta(seconds=10),
                created_at=ahora - timedelta(seconds=10),
            )
        )

        usuarios = {
            "admin": _usuario(session, "admin@aquaguard.dev", "admin", None),
            "cliente_a": _usuario(session, "a@aquaguard.dev", "client", a.id),
        }
        session.commit()
        return {
            "hotel": hotel,
            "vacio": vacio,
            "deposito": deposito,
            "entrada": entrada,
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


def _guardado(engine, sensor_id):
    with Session(engine) as session:
        return session.get(Sensor, sensor_id)


def _alta(site, **cambios):
    cuerpo = {
        "site_id": str(site.id),
        "external_id": "SENS-002",
        "name": "Salida",
        "min_pressure": 1.0,
        "max_pressure": 5.5,
        **cambios,
    }
    return cuerpo


# ---------------------------------------------------------
# B · GET /api/sites/{id}/sensors
# ---------------------------------------------------------
def test_un_cliente_ve_los_sensores_de_su_site(client, datos):
    _entrar(client, datos["cliente_a"])

    respuesta = client.get(f"/api/sites/{datos['hotel'].id}/sensors")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["total"] == 1
    sensor = cuerpo["items"][0]
    # Mismo formato que GET /api/sensors: estado y última lectura incluidos.
    assert sensor["name"] == "Entrada"
    assert sensor["external_id"] == "SENS-001"
    assert sensor["status"] == "ONLINE"
    assert sensor["last_seen_at"] is not None


def test_un_site_sin_sensores_devuelve_la_lista_vacia(client, datos):
    _entrar(client, datos["cliente_a"])

    cuerpo = client.get(f"/api/sites/{datos['vacio'].id}/sensors").json()

    assert cuerpo["total"] == 0
    assert cuerpo["items"] == []


def test_un_cliente_no_ve_los_sensores_de_un_site_ajeno(client, datos):
    _entrar(client, datos["cliente_a"])

    respuesta = client.get(f"/api/sites/{datos['deposito'].id}/sensors")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "SITE_NOT_FOUND"


def test_el_admin_ve_los_sensores_de_cualquier_site(client, datos):
    _entrar(client, datos["admin"])

    assert client.get(f"/api/sites/{datos['deposito'].id}/sensors").status_code == 200


def test_un_site_que_no_existe_da_404(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.get(f"/api/sites/{uuid4()}/sensors")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "SITE_NOT_FOUND"


# ---------------------------------------------------------
# C · POST /api/sensors
# ---------------------------------------------------------
def test_el_admin_da_de_alta_un_sensor(client, datos, engine):
    _entrar(client, datos["admin"])

    respuesta = client.post("/api/sensors", json=_alta(datos["hotel"], location="Sótano"))

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["external_id"] == "SENS-002"
    assert cuerpo["location"] == "Sótano"
    assert cuerpo["sensor_type"] == "PRESSURE"
    assert cuerpo["min_pressure"] == pytest.approx(1.0)
    assert cuerpo["max_pressure"] == pytest.approx(5.5)
    # Todavía no ha mandado nada.
    assert cuerpo["status"] == "OFFLINE"
    assert cuerpo["last_seen_at"] is None
    # Y está guardado de verdad.
    assert _guardado(engine, UUID(cuerpo["id"])).external_id == "SENS-002"


def test_unit_es_bar_si_no_se_envia(client, datos):
    _entrar(client, datos["admin"])

    cuerpo = client.post("/api/sensors", json=_alta(datos["hotel"])).json()

    assert cuerpo["unit"] == "bar"


def test_se_puede_dar_de_alta_un_sensor_de_caudal(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.post(
        "/api/sensors", json=_alta(datos["hotel"], sensor_type="FLOW", unit="m3/h")
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["sensor_type"] == "FLOW"
    assert respuesta.json()["unit"] == "m3/h"


def test_un_cliente_no_puede_dar_de_alta_sensores(client, datos, engine):
    _entrar(client, datos["cliente_a"])

    respuesta = client.post("/api/sensors", json=_alta(datos["hotel"]))

    assert respuesta.status_code == 403
    with Session(engine) as session:
        assert session.query(Sensor).count() == 1


def test_alta_en_un_site_que_no_existe_da_404(client, datos):
    _entrar(client, datos["admin"])

    cuerpo = _alta(datos["hotel"])
    cuerpo["site_id"] = str(uuid4())
    respuesta = client.post("/api/sensors", json=cuerpo)

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "SITE_NOT_FOUND"


def test_external_id_repetido_en_el_mismo_site_da_409(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.post(
        "/api/sensors", json=_alta(datos["hotel"], external_id="SENS-001")
    )

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "SENSOR_EXTERNAL_ID_TAKEN"


def test_el_mismo_external_id_vale_en_otro_site(client, datos):
    """Dos hoteles pueden tener cada uno su SENS-001."""
    _entrar(client, datos["admin"])

    respuesta = client.post(
        "/api/sensors", json=_alta(datos["deposito"], external_id="SENS-001")
    )

    assert respuesta.status_code == 201


@pytest.mark.parametrize(
    "cambio",
    [
        {"external_id": None},  # obligatorio
        {"min_pressure": 6.0, "max_pressure": 2.0},  # mínimo por encima del máximo
        {"max_pressure": 30.0},  # fuera del rango 0-25 bar
    ],
)
def test_un_alta_con_datos_malos_da_422(client, datos, cambio):
    _entrar(client, datos["admin"])

    cuerpo = {k: v for k, v in {**_alta(datos["hotel"]), **cambio}.items() if v is not None}
    respuesta = client.post("/api/sensors", json=cuerpo)

    assert respuesta.status_code == 422


# ---------------------------------------------------------
# C · PATCH /api/sensors/{id}
# ---------------------------------------------------------
def test_cambiar_solo_el_maximo_deja_el_minimo(client, datos, engine):
    _entrar(client, datos["admin"])

    respuesta = client.patch(f"/api/sensors/{datos['entrada'].id}", json={"max_pressure": 8.0})

    assert respuesta.status_code == 200
    assert respuesta.json()["max_pressure"] == pytest.approx(8.0)
    assert respuesta.json()["min_pressure"] == pytest.approx(1.5)
    assert float(_guardado(engine, datos["entrada"].id).high_threshold) == pytest.approx(8.0)


def test_un_umbral_que_choca_con_el_guardado_da_422(client, datos, engine):
    """
    El mínimo guardado es 1.5 y el máximo 6. Mandar solo `min_pressure: 7`
    es válido por sí solo, pero dejaría el mínimo por encima del máximo.
    """
    _entrar(client, datos["admin"])

    respuesta = client.patch(f"/api/sensors/{datos['entrada'].id}", json={"min_pressure": 7.0})

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "INVALID_THRESHOLDS"
    assert float(_guardado(engine, datos["entrada"].id).low_threshold) == pytest.approx(1.5)


def test_cambiar_nombre_y_ubicacion(client, datos):
    _entrar(client, datos["admin"])

    cuerpo = client.patch(
        f"/api/sensors/{datos['entrada'].id}",
        json={"name": "Entrada norte", "location": "Planta 0"},
    ).json()

    assert cuerpo["name"] == "Entrada norte"
    assert cuerpo["location"] == "Planta 0"
    # Lo que no se ha enviado no cambia.
    assert cuerpo["external_id"] == "SENS-001"


def test_un_nombre_vacio_da_422(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.patch(f"/api/sensors/{datos['entrada'].id}", json={"name": None})

    assert respuesta.status_code == 422


@pytest.mark.parametrize("campo", ["site_id", "sensor_type", "external_id"])
def test_no_se_puede_cambiar_ni_el_site_ni_el_tipo_ni_el_external_id(client, datos, campo):
    """Cambiarlos sería otro sensor (Ana, 03-10-2026)."""
    _entrar(client, datos["admin"])

    respuesta = client.patch(f"/api/sensors/{datos['entrada'].id}", json={campo: "X"})

    assert respuesta.status_code == 422


def test_un_cliente_no_puede_modificar_sensores(client, datos):
    _entrar(client, datos["cliente_a"])

    respuesta = client.patch(f"/api/sensors/{datos['entrada'].id}", json={"name": "Otro"})

    assert respuesta.status_code == 403


def test_modificar_un_sensor_que_no_existe_da_404(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.patch(f"/api/sensors/{uuid4()}", json={"name": "Otro"})

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "SENSOR_NOT_FOUND"


def test_dos_altas_simultaneas_con_el_mismo_external_id_dan_409(client, datos, monkeypatch):
    """
    Simula la carrera: la comprobación previa dice que está libre, pero la
    tabla ya lo tiene (lo ha guardado otra petición a la vez). Tiene que
    salir el mismo 409, no un 500.
    """
    from app.modules.sensors.repository import SensorRepository

    original = SensorRepository.external_id_taken
    llamadas = []

    def _primero_libre(self, site_id, external_id):
        # La primera vez está libre (la otra alta aún no se ha guardado);
        # después ya lo encuentra ocupado, como en la base de verdad.
        llamadas.append(1)
        return False if len(llamadas) == 1 else original(self, site_id, external_id)

    monkeypatch.setattr(SensorRepository, "external_id_taken", _primero_libre)
    _entrar(client, datos["admin"])

    respuesta = client.post("/api/sensors", json=_alta(datos["hotel"], external_id="SENS-001"))

    assert respuesta.status_code == 409
    assert respuesta.json()["error"]["code"] == "SENSOR_EXTERNAL_ID_TAKEN"


def test_otro_error_de_la_base_no_se_disfraza_de_409(client, datos, monkeypatch):
    """
    Comentario de Daru en la #115: si la tabla rechaza el alta por otro
    motivo (aquí, se simula un error cualquiera al guardar), no debe
    salir como "external_id repetido".
    """
    from sqlalchemy.exc import IntegrityError

    from app.modules.sensors.repository import SensorRepository

    def _revienta(self, **campos):
        raise IntegrityError("INSERT", {}, Exception("FOREIGN KEY constraint failed"))

    monkeypatch.setattr(SensorRepository, "create", _revienta)
    _entrar(client, datos["admin"])

    with pytest.raises(IntegrityError):
        client.post("/api/sensors", json=_alta(datos["hotel"], external_id="NUEVO"))


@pytest.mark.parametrize("ruta", ["alta", "edicion"])
def test_un_nombre_de_solo_espacios_da_422(client, datos, ruta):
    """Comentario de Daru en la #115: min_length=1 no recortaba los espacios."""
    _entrar(client, datos["admin"])

    if ruta == "alta":
        respuesta = client.post("/api/sensors", json=_alta(datos["hotel"], name="   "))
    else:
        respuesta = client.patch(f"/api/sensors/{datos['entrada'].id}", json={"name": "   "})

    assert respuesta.status_code == 422


def test_los_espacios_de_los_extremos_del_nombre_se_quitan(client, datos):
    _entrar(client, datos["admin"])

    cuerpo = client.post("/api/sensors", json=_alta(datos["hotel"], name="  Salida  ")).json()

    assert cuerpo["name"] == "Salida"
