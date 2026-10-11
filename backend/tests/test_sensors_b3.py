"""
Sensores (B3, issue #139): planta en el alta y la edición, `health`,
`last_value` y el filtro `?health=`.
"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
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
from app.modules.sensors.status import calcular_salud
from app.modules.sites.model import Site
from app.modules.users.model import User
from app.shared.enums import SensorHealth, SensorStatus

AHORA = datetime.now(timezone.utc)


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


def _sensor(site, nombre, floor=0):
    return Sensor(
        site_id=site.id,
        external_id=f"S-{nombre}",
        name=nombre,
        floor=floor,
        unit="bar",
        low_threshold=Decimal("1"),
        high_threshold=Decimal("9"),
    )


def _lectura(sensor, valor, llego_hace, medida_hace=None):
    return Reading(
        sensor_id=sensor.id,
        value=Decimal(valor),
        unit="bar",
        recorded_at=AHORA - (medida_hace if medida_hace is not None else llego_hace),
        created_at=AHORA - llego_hace,
    )


def _alerta(sensor, severidad, estado="ACTIVE", reconocida=False):
    return Alert(
        sensor_id=sensor.id,
        alert_type="LOW_PRESSURE",
        severity=severidad,
        message="Presión baja",
        status=estado,
        acknowledged_at=AHORA if reconocida else None,
    )


@pytest.fixture()
def datos(engine):
    """
    Hotel Sol, edificio Torre (6 plantas y 2 sótanos: de la -2 a la 5):

    - Bien:    lecturas recientes, sin alertas                  → OK
    - Aviso:   WARNING abierta (y una CRITICAL resuelta)        → WARNING
    - Crítico: CRITICAL abierta y reconocida, y una WARNING     → CRITICAL
    - Mudo:    nunca ha enviado, con una CRITICAL abierta       → OFFLINE
    - Viejo:   última lectura hace 10 minutos                   → OFFLINE

    Colegio Luna, edificio Patio: Ajeno, OK. Un cliente de Sol no lo ve.
    """
    with Session(engine, expire_on_commit=False) as s:
        sol, luna = Organization(name="Hotel Sol"), Organization(name="Colegio Luna")
        s.add_all([sol, luna])
        s.flush()
        torre = Site(organization_id=sol.id, name="Torre", floors=6, basements=2)
        patio = Site(organization_id=luna.id, name="Patio")
        s.add_all([torre, patio])
        s.flush()

        bien, aviso, critico = _sensor(torre, "Bien", 3), _sensor(torre, "Aviso"), _sensor(torre, "Crítico")
        mudo, viejo, ajeno = _sensor(torre, "Mudo", -2), _sensor(torre, "Viejo"), _sensor(patio, "Ajeno")
        s.add_all([bien, aviso, critico, mudo, viejo, ajeno])
        s.flush()

        s.add_all([
            # La que llegó la última es la de 3.4, aunque se midiera antes.
            _lectura(bien, "2.0", timedelta(minutes=2), medida_hace=timedelta(0)),
            _lectura(bien, "3.4", timedelta(minutes=1), medida_hace=timedelta(minutes=3)),
            _lectura(aviso, "1.2", timedelta(minutes=1)),
            _lectura(critico, "0.4", timedelta(minutes=1)),
            _lectura(viejo, "5.0", timedelta(minutes=10)),
            _lectura(ajeno, "3.0", timedelta(minutes=1)),
            _alerta(aviso, "WARNING"),
            _alerta(aviso, "CRITICAL", estado="RESOLVED"),
            _alerta(critico, "CRITICAL", reconocida=True),
            _alerta(critico, "WARNING"),
            _alerta(mudo, "CRITICAL"),
        ])

        cliente = User(organization_id=sol.id, email="cliente@sol.dev", name="Cliente",
                       password_hash="x", role="client")
        admin = User(email="admin@aquaguard.dev", name="Admin", password_hash="x",
                     role="admin")
        s.add_all([cliente, admin])
        s.commit()
        return {"sol": sol, "luna": luna, "torre": torre, "patio": patio,
                "bien": bien, "aviso": aviso, "critico": critico, "mudo": mudo,
                "viejo": viejo, "ajeno": ajeno, "cliente": cliente, "admin": admin}


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


@pytest.fixture()
def admin(client, datos):
    _entrar(client, datos["admin"])
    return client


@pytest.fixture()
def cliente(client, datos):
    _entrar(client, datos["cliente"])
    return client


def _codigo(respuesta):
    return respuesta.json()["error"]["code"]


def _por_nombre(cuerpo):
    return {s["name"]: s for s in cuerpo["items"]}


def _nuevo(datos, **cambios):
    cuerpo = {"site_id": str(datos["torre"].id), "external_id": "S-nuevo",
              "name": "Nuevo", "min_pressure": 1.5, "max_pressure": 6}
    return {**cuerpo, **cambios}


# ---------------------------------------------------------
# REGLA DE SALUD (sin base de datos)
# ---------------------------------------------------------
@pytest.mark.parametrize(
    ("estado", "severidades", "esperada"),
    [
        (SensorStatus.OFFLINE, {"CRITICAL"}, SensorHealth.OFFLINE),
        (SensorStatus.OFFLINE, set(), SensorHealth.OFFLINE),
        (SensorStatus.ONLINE, {"CRITICAL", "WARNING"}, SensorHealth.CRITICAL),
        (SensorStatus.ONLINE, {"WARNING"}, SensorHealth.WARNING),
        (SensorStatus.ONLINE, set(), SensorHealth.OK),
    ],
)
def test_regla_de_salud(estado, severidades, esperada):
    assert calcular_salud(estado, severidades) == esperada


# ---------------------------------------------------------
# HEALTH Y LAST_VALUE EN LA RESPUESTA
# ---------------------------------------------------------
def test_la_lista_trae_salud_y_ultimo_valor(admin):
    sensores = _por_nombre(admin.get("/api/sensors").json())

    salud = {nombre: s["health"] for nombre, s in sensores.items()}
    assert salud == {
        "Bien": "OK", "Aviso": "WARNING", "Crítico": "CRITICAL",
        "Mudo": "OFFLINE", "Viejo": "OFFLINE", "Ajeno": "OK",
    }
    # La última que llegó, aunque se midiera antes que la otra.
    assert sensores["Bien"]["last_value"] == 3.4
    assert sensores["Viejo"]["last_value"] == 5.0
    assert sensores["Mudo"]["last_value"] is None
    assert sensores["Mudo"]["last_seen_at"] is None


def test_la_ficha_y_los_sensores_del_edificio_traen_lo_mismo(admin, datos):
    lista = _por_nombre(admin.get("/api/sensors").json())
    del_edificio = _por_nombre(
        admin.get(f"/api/sites/{datos['torre'].id}/sensors").json()
    )
    ficha = admin.get(f"/api/sensors/{datos['critico'].id}").json()

    for nombre in ("Bien", "Aviso", "Crítico", "Mudo", "Viejo"):
        for campo in ("health", "last_value", "floor"):
            assert del_edificio[nombre][campo] == lista[nombre][campo]
    assert (ficha["health"], ficha["last_value"]) == ("CRITICAL", 0.4)


def test_la_lista_no_hace_mas_consultas_con_mas_sensores(admin, datos, engine):
    """La salud y el último valor salen en bloque, no por sensor."""
    def consultas():
        contador = []
        escuchar = lambda *args: contador.append(1)  # noqa: E731
        event.listen(engine, "before_cursor_execute", escuchar)
        try:
            assert admin.get("/api/sensors").status_code == 200
        finally:
            event.remove(engine, "before_cursor_execute", escuchar)
        return len(contador)

    con_seis = consultas()
    with Session(engine) as s:
        torre = s.get(Site, datos["torre"].id)
        for n in range(6):
            sensor = _sensor(torre, f"Extra {n}")
            s.add(sensor)
            s.flush()
            s.add_all([_lectura(sensor, "3", timedelta(minutes=1)),
                       _alerta(sensor, "WARNING")])
        s.commit()
    assert consultas() == con_seis


# ---------------------------------------------------------
# FILTRO ?health=
# ---------------------------------------------------------
@pytest.mark.parametrize(
    ("salud", "esperados"),
    [
        ("OK", {"Bien", "Ajeno"}),
        ("WARNING", {"Aviso"}),
        ("CRITICAL", {"Crítico"}),
        ("OFFLINE", {"Mudo", "Viejo"}),
    ],
)
def test_filtrar_por_salud(admin, salud, esperados):
    cuerpo = admin.get("/api/sensors", params={"health": salud}).json()

    assert set(_por_nombre(cuerpo)) == esperados
    assert cuerpo["total"] == len(esperados)
    assert all(s["health"] == salud for s in cuerpo["items"])


def test_el_filtro_de_salud_respeta_la_organizacion(cliente):
    cuerpo = cliente.get("/api/sensors", params={"health": "OK"}).json()
    assert set(_por_nombre(cuerpo)) == {"Bien"}


def test_el_filtro_de_salud_se_suma_a_los_demas(admin, datos):
    cuerpo = admin.get(
        "/api/sensors", params={"health": "OK", "site_id": str(datos["patio"].id)}
    ).json()
    assert set(_por_nombre(cuerpo)) == {"Ajeno"}


def test_una_salud_que_no_existe_da_422(admin):
    assert admin.get("/api/sensors", params={"health": "REGULAR"}).status_code == 422


# ---------------------------------------------------------
# PLANTA EN EL ALTA
# ---------------------------------------------------------
def test_alta_sin_planta_va_a_la_baja(admin, datos):
    respuesta = admin.post("/api/sensors", json=_nuevo(datos))
    assert respuesta.status_code == 201
    assert respuesta.json()["floor"] == 0
    assert (respuesta.json()["health"], respuesta.json()["last_value"]) == ("OFFLINE", None)


@pytest.mark.parametrize("planta", [-2, 5])
def test_alta_en_la_planta_mas_baja_y_la_mas_alta(admin, datos, planta):
    respuesta = admin.post("/api/sensors", json=_nuevo(datos, floor=planta))
    assert respuesta.status_code == 201
    assert respuesta.json()["floor"] == planta


@pytest.mark.parametrize("planta", [-3, 6])
def test_alta_en_una_planta_que_no_existe_da_422(admin, datos, engine, planta):
    respuesta = admin.post("/api/sensors", json=_nuevo(datos, floor=planta))

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "FLOOR_OUT_OF_SITE"
    with Session(engine) as s:
        assert s.query(Sensor).filter_by(external_id="S-nuevo").count() == 0


def test_alta_en_un_site_que_no_existe_sigue_dando_404(admin, datos):
    respuesta = admin.post("/api/sensors", json=_nuevo(datos, site_id=str(uuid.uuid4())))
    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "SITE_NOT_FOUND"


# ---------------------------------------------------------
# PLANTA EN LA EDICIÓN
# ---------------------------------------------------------
def test_mover_un_sensor_de_planta(admin, datos):
    url = f"/api/sensors/{datos['bien'].id}"
    respuesta = admin.patch(url, json={"floor": -1})

    assert respuesta.status_code == 200
    assert respuesta.json()["floor"] == -1
    assert admin.get(url).json()["floor"] == -1


@pytest.mark.parametrize("planta", [-3, 6])
def test_mover_a_una_planta_que_no_existe_da_422(admin, datos, planta):
    url = f"/api/sensors/{datos['bien'].id}"
    respuesta = admin.patch(url, json={"floor": planta})

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "FLOOR_OUT_OF_SITE"
    assert admin.get(url).json()["floor"] == 3


def test_la_planta_no_puede_quedar_vacia(admin, datos):
    respuesta = admin.patch(f"/api/sensors/{datos['bien'].id}", json={"floor": None})
    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "INVALID_FLOOR"


def test_editar_sin_tocar_la_planta_no_la_cambia(admin, datos):
    respuesta = admin.patch(f"/api/sensors/{datos['mudo'].id}", json={"name": "Sótano"})
    assert respuesta.status_code == 200
    assert (respuesta.json()["name"], respuesta.json()["floor"]) == ("Sótano", -2)


def test_un_cliente_no_puede_mover_sensores(cliente, datos):
    respuesta = cliente.patch(f"/api/sensors/{datos['bien'].id}", json={"floor": 1})
    assert respuesta.status_code == 403


def test_tras_mover_un_sensor_el_edificio_no_deja_quitar_esa_planta(admin, datos):
    """La regla de la B2 ve la planta nueva del sensor."""
    admin.patch(f"/api/sensors/{datos['bien'].id}", json={"floor": 5})

    respuesta = admin.patch(f"/api/sites/{datos['torre'].id}", json={"floors": 5})
    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "FLOOR_OUT_OF_SITE"
