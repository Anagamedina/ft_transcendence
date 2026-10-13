"""
B7 (#143): histórico con rango y orden, y serie agregada para la gráfica.

Usa el `engine` de conftest.py, así que cada test corre en SQLite y en
PostgreSQL: la serie agrupa con `date_bin` en PostgreSQL y con aritmética
de segundos en SQLite, y las dos tienen que dar los mismos tramos.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.readings.repository import SERIES_ORIGIN
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

DOS_HORAS = timedelta(hours=2)


def _inicio_de_tramo(momento: datetime) -> datetime:
    """El tramo de 2 h que contiene `momento`, alineado como en la serie."""
    return momento - (momento - SERIES_ORIGIN) % DOS_HORAS


# Dos tramos seguidos de hace un día, lejos de los bordes de los 7 días.
T1 = _inicio_de_tramo(datetime.now(timezone.utc) - timedelta(days=1))
T2 = T1 + DOS_HORAS
ANTIGUA = T1 - timedelta(days=10)


def _organizacion(db: Session, nombre: str) -> dict:
    org = Organization(name=nombre)
    db.add(org)
    db.flush()
    usuario = User(
        organization_id=org.id,
        email=f"client@{nombre.lower()}.test",
        name="Client",
        password_hash="hashed",
        role="client",
    )
    site = Site(organization_id=org.id, name=f"Edificio {nombre}")
    db.add_all([usuario, site])
    db.flush()
    sensor = Sensor(
        site_id=site.id,
        external_id=f"S-{nombre}",
        name=f"Sensor {nombre}",
        low_threshold=Decimal("1.5"),
        high_threshold=Decimal("6"),
    )
    db.add(sensor)
    db.flush()
    return {"user": usuario, "sensor": sensor}


def _lectura(sensor, valor, momento):
    return Reading(
        sensor_id=sensor.id, value=Decimal(valor), unit="bar", recorded_at=momento
    )


@pytest.fixture()
def datos(engine):
    with Session(engine, expire_on_commit=False) as db:
        a = _organizacion(db, "A")
        b = _organizacion(db, "B")
        sa = a["sensor"]
        db.add_all(
            [
                # T1: tres lecturas, media 3
                _lectura(sa, "2.000", T1 + timedelta(minutes=10)),
                _lectura(sa, "3.000", T1 + timedelta(minutes=20)),
                _lectura(sa, "4.000", T1 + timedelta(minutes=40)),
                # T2: una
                _lectura(sa, "5.000", T2 + timedelta(minutes=5)),
                # Fuera de los 7 días
                _lectura(sa, "9.000", ANTIGUA),
                # Otra organización
                _lectura(b["sensor"], "7.000", T1 + timedelta(minutes=10)),
            ]
        )
        db.commit()
        return {"a": a, "b": b}


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


def _fecha(texto: str) -> datetime:
    return datetime.fromisoformat(texto.replace("Z", "+00:00"))


def _iso(momento: datetime) -> str:
    return momento.isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------
# Histórico: orden y rango
# ---------------------------------------------------------
def test_el_historico_va_de_la_mas_reciente_a_la_mas_antigua(client, datos):
    _entrar(client, datos["a"]["user"])

    items = client.get(f"/api/sensors/{datos['a']['sensor'].id}/readings").json()["items"]

    assert [i["pressure"] for i in items] == [5.0, 4.0, 3.0, 2.0, 9.0]


def test_order_asc_va_de_la_mas_antigua_a_la_mas_reciente(client, datos):
    _entrar(client, datos["a"]["user"])

    items = client.get(
        f"/api/sensors/{datos['a']['sensor'].id}/readings", params={"order": "asc"}
    ).json()["items"]

    assert [i["pressure"] for i in items] == [9.0, 2.0, 3.0, 4.0, 5.0]


def test_from_y_to_limitan_el_historico_sin_incluir_to(client, datos):
    _entrar(client, datos["a"]["user"])

    cuerpo = client.get(
        f"/api/sensors/{datos['a']['sensor'].id}/readings",
        params={"from": _iso(T1), "to": _iso(T2)},
    ).json()

    assert cuerpo["total"] == 3
    assert [i["pressure"] for i in cuerpo["items"]] == [4.0, 3.0, 2.0]


def test_from_posterior_a_to_da_422(client, datos):
    _entrar(client, datos["a"]["user"])

    respuesta = client.get(
        f"/api/sensors/{datos['a']['sensor'].id}/readings",
        params={"from": _iso(T2), "to": _iso(T1)},
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "INVALID_DATE_RANGE"


def test_un_order_desconocido_da_422(client, datos):
    _entrar(client, datos["a"]["user"])

    respuesta = client.get(
        f"/api/sensors/{datos['a']['sensor'].id}/readings", params={"order": "up"}
    )

    assert respuesta.status_code == 422


# ---------------------------------------------------------
# Serie para la gráfica
# ---------------------------------------------------------
def test_la_serie_agrupa_en_tramos_con_media_minimo_y_maximo(client, datos):
    _entrar(client, datos["a"]["user"])

    cuerpo = client.get(f"/api/sensors/{datos['a']['sensor'].id}/readings/series").json()

    puntos = [
        {**p, "t": _fecha(p["t"])} for p in cuerpo["points"]
    ]
    assert puntos == [
        {"t": T1, "avg": 3.0, "min": 2.0, "max": 4.0},
        {"t": T2, "avg": 5.0, "min": 5.0, "max": 5.0},
    ]


def test_la_serie_trae_los_umbrales_y_el_periodo(client, datos):
    _entrar(client, datos["a"]["user"])

    cuerpo = client.get(f"/api/sensors/{datos['a']['sensor'].id}/readings/series").json()

    assert cuerpo["min_pressure"] == 1.5
    assert cuerpo["max_pressure"] == 6.0
    assert cuerpo["unit"] == "bar"
    assert cuerpo["bucket"] == "2h"
    assert _fecha(cuerpo["to"]) - _fecha(cuerpo["from"]) == timedelta(days=7)


def test_days_y_bucket_cambian_la_serie(client, datos):
    _entrar(client, datos["a"]["user"])

    cuerpo = client.get(
        f"/api/sensors/{datos['a']['sensor'].id}/readings/series",
        params={"days": 30, "bucket": "1d"},
    ).json()

    # 30 días ya incluyen la lectura antigua; en tramos de un día, T1 y T2
    # pueden caer en el mismo día o en dos, así que se mira el total.
    assert sum(p["max"] == 9.0 for p in cuerpo["points"]) == 1
    assert min(p["min"] for p in cuerpo["points"]) == 2.0


def test_un_sensor_sin_lecturas_da_una_serie_vacia(client, engine, datos):
    with Session(engine) as db:
        site_id = db.get(Sensor, datos["a"]["sensor"].id).site_id
        vacio = Sensor(
            site_id=site_id,
            external_id="S-vacio",
            name="Vacío",
            low_threshold=Decimal("1"),
            high_threshold=Decimal("5"),
        )
        db.add(vacio)
        db.commit()
        vacio_id = vacio.id
    _entrar(client, datos["a"]["user"])

    cuerpo = client.get(f"/api/sensors/{vacio_id}/readings/series").json()

    assert cuerpo["points"] == []


def test_la_serie_de_otra_organizacion_da_404(client, datos):
    _entrar(client, datos["a"]["user"])

    respuesta = client.get(f"/api/sensors/{datos['b']['sensor'].id}/readings/series")

    assert respuesta.status_code == 404
    assert respuesta.json()["error"]["code"] == "SENSOR_NOT_FOUND"


def test_la_serie_sin_sesion_da_401(client, datos):
    respuesta = client.get(f"/api/sensors/{datos['a']['sensor'].id}/readings/series")

    assert respuesta.status_code == 401


def test_demasiados_puntos_da_422(client, datos):
    _entrar(client, datos["a"]["user"])

    respuesta = client.get(
        f"/api/sensors/{datos['a']['sensor'].id}/readings/series",
        params={"days": 30, "bucket": "15m"},
    )

    assert respuesta.status_code == 422
    assert respuesta.json()["error"]["code"] == "TOO_MANY_POINTS"


@pytest.mark.parametrize(
    "params", [{"days": 0}, {"days": 31}, {"bucket": "5m"}]
)
def test_parametros_no_validos_dan_422(client, datos, params):
    _entrar(client, datos["a"]["user"])

    respuesta = client.get(
        f"/api/sensors/{datos['a']['sensor'].id}/readings/series", params=params
    )

    assert respuesta.status_code == 422
