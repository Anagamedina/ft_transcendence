"""
Importar sensores desde un CSV (`POST /api/sensors/import`), módulo «Data
export and import»: validación por fila, todo o nada, vista previa y el
límite del contrato.
"""

import uuid
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.organizations.model import Organization
from app.modules.sensors.importer import MAX_IMPORT_ROWS
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

URL = "/api/sensors/import"
CABECERA = "external_id,name,location,floor,min_pressure,max_pressure"


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


@pytest.fixture()
def datos(engine):
    """
    Hotel Sol, cliente con 5 sensores contratados. Su edificio Torre va de
    la planta -1 a la 3 y ya tiene el sensor «T-0». Colegio Luna, en
    prueba (sin límite), con el edificio Patio vacío.
    """
    with Session(engine, expire_on_commit=False) as s:
        sol = Organization(name="Hotel Sol", status="ACTIVE", contracted_sensors=5)
        luna = Organization(name="Colegio Luna", status="TRIAL")
        s.add_all([sol, luna])
        s.flush()
        torre = Site(organization_id=sol.id, name="Torre", floors=4, basements=1)
        patio = Site(organization_id=luna.id, name="Patio", floors=2)
        s.add_all([torre, patio])
        s.flush()
        s.add(
            Sensor(
                site_id=torre.id,
                external_id="T-0",
                name="Ya instalado",
                unit="bar",
                low_threshold=Decimal("1"),
                high_threshold=Decimal("6"),
            )
        )
        admin = User(email="admin@aquaguard.dev", name="Admin", password_hash="x", role="admin")
        cliente = User(
            organization_id=sol.id,
            email="cliente@sol.dev",
            name="Cliente",
            password_hash="x",
            role="client",
        )
        s.add_all([admin, cliente])
        s.commit()
        return {"torre": torre, "patio": patio, "admin": admin, "cliente": cliente}


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


@pytest.fixture()
def admin(client, datos):
    client.cookies.set(SESSION_COOKIE, create_session_token(datos["admin"].id))
    return client


def _subir(client, site, contenido, dry_run=None, encoding="utf-8"):
    datos = {"site_id": str(site.id)}
    if dry_run is not None:
        datos["dry_run"] = str(dry_run).lower()
    cuerpo = contenido.encode(encoding) if isinstance(contenido, str) else contenido
    return client.post(URL, data=datos, files={"file": ("sensores.csv", cuerpo, "text/csv")})


def _csv(*filas, cabecera=CABECERA):
    return "\n".join([cabecera, *filas]) + "\n"


def _sensores(engine, site):
    with Session(engine) as s:
        return {
            x.external_id: x
            for x in s.scalars(select(Sensor).where(Sensor.site_id == site.id))
        }


def _codigo(respuesta):
    return respuesta.json()["error"]["code"]


# ---------------------------------------------------------
# IMPORTAR
# ---------------------------------------------------------
def test_importa_todos_los_sensores(admin, engine, datos):
    respuesta = _subir(
        admin,
        datos["torre"],
        _csv(
            "T-1,Cocina,Planta 1 - Cocina,1,1.5,6",
            "T-2,Sótano,,-1,2,7.5",
        ),
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert (cuerpo["dry_run"], cuerpo["created"], cuerpo["site_name"]) == (False, 2, "Torre")
    assert [x["line"] for x in cuerpo["sensors"]] == [2, 3]

    sensores = _sensores(engine, datos["torre"])
    assert set(sensores) == {"T-0", "T-1", "T-2"}
    cocina = sensores["T-1"]
    assert (cocina.name, cocina.location, cocina.floor) == ("Cocina", "Planta 1 - Cocina", 1)
    assert (cocina.low_threshold, cocina.high_threshold) == (Decimal("1.5"), Decimal("6"))
    assert (cocina.unit, cocina.sensor_type) == ("bar", "PRESSURE")
    assert sensores["T-2"].location is None


def test_acepta_el_csv_de_excel_en_espanol(admin, engine, datos):
    """Punto y coma, coma decimal, Windows-1252 y columnas en otro orden."""
    contenido = _csv(
        "1,5;6;Baño;T-9",
        cabecera="Min_Pressure;MAX_PRESSURE;Name;External_ID",
    )
    respuesta = _subir(admin, datos["torre"], contenido, encoding="cp1252")

    assert respuesta.status_code == 201
    baño = _sensores(engine, datos["torre"])["T-9"]
    assert (baño.name, baño.floor, baño.low_threshold) == ("Baño", 0, Decimal("1.5"))


def test_las_lineas_en_blanco_no_cuentan(admin, engine, datos):
    respuesta = _subir(admin, datos["torre"], _csv("T-1,Cocina,,0,1,6", "", "  ,  ,,,,"))
    assert respuesta.status_code == 201
    assert respuesta.json()["created"] == 1


def test_la_vista_previa_no_crea_nada(admin, engine, datos):
    respuesta = _subir(admin, datos["torre"], _csv("T-1,Cocina,,0,1,6"), dry_run=True)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert (cuerpo["dry_run"], cuerpo["created"]) == (True, 0)
    assert cuerpo["sensors"][0]["external_id"] == "T-1"
    assert set(_sensores(engine, datos["torre"])) == {"T-0"}


# ---------------------------------------------------------
# ERRORES POR FILA: TODOS A LA VEZ Y NO SE CREA NINGUNO
# ---------------------------------------------------------
def test_devuelve_todos_los_errores_y_no_crea_ninguno(admin, engine, datos):
    respuesta = _subir(
        admin,
        datos["torre"],
        _csv(
            "T-1,Bien,,0,1,6",  # 2: correcta, pero no entra porque otras fallan
            "T-2,,,0,1,6",  # 3: sin nombre
            "T-3,Letras,,0,uno,6",  # 4: no es un número
            "T-4,Fuera,,0,1,30",  # 5: fuera de rango
            "T-5,Al revés,,0,8,2",  # 6: mínimo mayor que máximo
            "T-6,Planta,,primera,1,6",  # 7: planta que no es un número
            "T-7,Ático,,9,1,6",  # 8: planta que el edificio no tiene
            "T-1,Repe,,0,1,6",  # 9: repetida en el archivo
            "T-0,Existe,,0,1,6",  # 10: ya está en el edificio
        ),
    )

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "IMPORT_INVALID_ROWS"
    errores = {(e["row"], e["field"]) for e in respuesta.json()["error"]["details"]}
    assert errores == {
        (3, "name"),
        (4, "min_pressure"),
        (5, "max_pressure"),
        (6, "min_pressure"),
        (7, "floor"),
        (8, "floor"),
        (9, "external_id"),
        (10, "external_id"),
    }
    assert "8 filas tienen errores" in respuesta.json()["error"]["message"]
    assert set(_sensores(engine, datos["torre"])) == {"T-0"}


def test_el_error_de_planta_dice_las_que_tiene_el_edificio(admin, datos):
    respuesta = _subir(admin, datos["torre"], _csv("T-1,Ático,,9,1,6"))
    error = respuesta.json()["error"]["details"][0]
    assert error["message"] == "El edificio va de la planta -1 a la 3: la planta 9 no existe."


# ---------------------------------------------------------
# ERRORES DEL ARCHIVO ENTERO
# ---------------------------------------------------------
@pytest.mark.parametrize(
    ("contenido", "codigo"),
    [
        (b"", "EMPTY_FILE"),
        (b"\x00\x01\x02binario\xff", "UNSUPPORTED_FILE_TYPE"),
        ("external_id,name\nT-1,Cocina\n", "IMPORT_MISSING_COLUMNS"),
        (CABECERA + "\n", "IMPORT_NO_ROWS"),
    ],
)
def test_archivo_que_no_vale(admin, engine, datos, contenido, codigo):
    respuesta = _subir(admin, datos["torre"], contenido)
    assert respuesta.status_code == 422
    assert _codigo(respuesta) == codigo
    assert set(_sensores(engine, datos["torre"])) == {"T-0"}


def test_faltan_columnas_dice_cuales(admin, datos):
    respuesta = _subir(admin, datos["torre"], "external_id,name\nT-1,Cocina\n")
    faltan = [e["field"] for e in respuesta.json()["error"]["details"]]
    assert faltan == ["min_pressure", "max_pressure"]


def test_mas_filas_de_las_permitidas(admin, datos):
    filas = [f"T-{i},Sensor {i},,0,1,6" for i in range(MAX_IMPORT_ROWS + 1)]
    respuesta = _subir(admin, datos["patio"], _csv(*filas))
    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "IMPORT_TOO_MANY_ROWS"


# ---------------------------------------------------------
# LÍMITE DEL CONTRATO, EDIFICIO Y PERMISOS
# ---------------------------------------------------------
def test_caben_justo_los_contratados(admin, engine, datos):
    """Tiene 1 de 5: caben 4."""
    filas = [f"T-{i},Sensor {i},,0,1,6" for i in range(1, 5)]
    assert _subir(admin, datos["torre"], _csv(*filas)).status_code == 201
    assert len(_sensores(engine, datos["torre"])) == 5


def test_pasarse_del_contrato_da_409_y_no_crea_ninguno(admin, engine, datos):
    filas = [f"T-{i},Sensor {i},,0,1,6" for i in range(1, 6)]
    respuesta = _subir(admin, datos["torre"], _csv(*filas))

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "SENSOR_LIMIT_REACHED"
    assert "caben 4 más y el archivo trae 5" in respuesta.json()["error"]["message"]
    assert set(_sensores(engine, datos["torre"])) == {"T-0"}


def test_en_prueba_no_hay_limite_de_sensores(admin, engine, datos):
    filas = [f"P-{i},Sensor {i},,0,1,6" for i in range(20)]
    assert _subir(admin, datos["patio"], _csv(*filas)).status_code == 201
    assert len(_sensores(engine, datos["patio"])) == 20


def test_edificio_que_no_existe_da_404(admin, datos):
    falso = Site(id=uuid.uuid4(), organization_id=uuid.uuid4(), name="X")
    respuesta = _subir(admin, falso, _csv("T-1,Cocina,,0,1,6"))
    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "SITE_NOT_FOUND"


def test_un_cliente_no_puede_importar(client, engine, datos):
    client.cookies.set(SESSION_COOKIE, create_session_token(datos["cliente"].id))
    respuesta = _subir(client, datos["torre"], _csv("T-1,Cocina,,0,1,6"))
    assert respuesta.status_code == 403
    assert set(_sensores(engine, datos["torre"])) == {"T-0"}


def test_sin_sesion_da_401(client, datos):
    assert _subir(client, datos["torre"], _csv("T-1,Cocina,,0,1,6")).status_code == 401


def test_la_importacion_no_cambia_el_alta_de_uno(admin, engine, datos):
    """El límite de 1 en 1 sigue igual: con 5 de 5, el alta normal da 409."""
    filas = [f"T-{i},Sensor {i},,0,1,6" for i in range(1, 5)]
    _subir(admin, datos["torre"], _csv(*filas))
    respuesta = admin.post(
        "/api/sensors",
        json={
            "site_id": str(datos["torre"].id),
            "external_id": "T-9",
            "name": "Otro",
            "min_pressure": 1,
            "max_pressure": 6,
        },
    )
    assert respuesta.status_code == 409
    assert "ya tiene 5 sensores" in respuesta.json()["error"]["message"]
    with Session(engine) as s:
        assert s.scalar(select(func.count()).select_from(Sensor)) == 5
