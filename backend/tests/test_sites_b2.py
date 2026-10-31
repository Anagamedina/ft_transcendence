"""
Edificios (B2, issue #139): alta, edición y borrado, plantas y tipo, y los
campos calculados `sensor_count` y `status`.
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.alerts.model import Alert
from app.modules.documents.model import Document
from app.modules.organizations.model import Organization
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.sites.service import SiteService
from app.modules.users.model import User


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


def _sensor(site, n, floor=0):
    return Sensor(
        site_id=site.id,
        external_id=f"S-{n}",
        name=f"Sensor {n}",
        floor=floor,
        unit="bar",
        low_threshold=Decimal("1"),
        high_threshold=Decimal("9"),
    )


@pytest.fixture()
def datos(engine):
    """
    Hotel Sol con tres edificios:
    - Torre: 6 plantas y 2 sótanos, sensores en la planta -2 y en la 5,
      una alerta WARNING y una CRITICAL abiertas → CRITICAL.
    - Anexo: un sensor con solo una WARNING abierta (y una CRITICAL
      resuelta, que no cuenta) → WARNING.
    - Vacío: sin sensores → OK.
    """
    with Session(engine, expire_on_commit=False) as s:
        sol = Organization(name="Hotel Sol")
        luna = Organization(name="Colegio Luna")
        s.add_all([sol, luna])
        s.flush()

        torre = Site(organization_id=sol.id, name="Torre", floors=6, basements=2,
                     building_type="HOTEL")
        anexo = Site(organization_id=sol.id, name="Anexo")
        vacio = Site(organization_id=sol.id, name="Vacío")
        patio = Site(organization_id=luna.id, name="Patio")
        s.add_all([torre, anexo, vacio, patio])
        s.flush()

        abajo, arriba, del_anexo = _sensor(torre, 1, -2), _sensor(torre, 2, 5), _sensor(anexo, 3)
        s.add_all([abajo, arriba, del_anexo])
        s.flush()
        for sensor, severidad, estado in [
            (abajo, "WARNING", "ACTIVE"),
            (arriba, "CRITICAL", "ACTIVE"),
            (del_anexo, "WARNING", "ACTIVE"),
            (del_anexo, "CRITICAL", "RESOLVED"),
        ]:
            s.add(Alert(sensor_id=sensor.id, alert_type="LOW_PRESSURE",
                        severity=severidad, message="Presión baja", status=estado))

        cliente = User(organization_id=sol.id, email="cliente@sol.dev", name="Cliente",
                       password_hash="x", role="client")
        admin = User(email="admin@aquaguard.dev", name="Admin", password_hash="x",
                     role="admin")
        s.add_all([cliente, admin])
        s.commit()
        return {"sol": sol, "luna": luna, "torre": torre, "anexo": anexo,
                "vacio": vacio, "patio": patio, "cliente": cliente, "admin": admin}


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


def _codigo(respuesta):
    return respuesta.json()["error"]["code"]


def _por_nombre(cuerpo):
    return {s["name"]: s for s in cuerpo["items"]}


# ---------------------------------------------------------
# CAMPOS NUEVOS EN LA LECTURA
# ---------------------------------------------------------
def test_la_lista_trae_plantas_tipo_sensores_y_estado(admin, datos):
    sites = _por_nombre(admin.get("/api/sites").json())

    torre = sites["Torre"]
    assert (torre["floors"], torre["basements"], torre["building_type"]) == (6, 2, "HOTEL")
    assert torre["sensor_count"] == 2
    assert torre["status"] == "CRITICAL"
    assert sites["Anexo"]["status"] == "WARNING"  # la CRITICAL resuelta no cuenta
    assert sites["Vacío"]["status"] == "OK"
    assert sites["Vacío"]["sensor_count"] == 0
    # Un site antiguo, sin plantas ni tipo, sale con los valores por defecto
    assert (sites["Anexo"]["floors"], sites["Anexo"]["basements"],
            sites["Anexo"]["building_type"]) == (1, 0, "OTHER")


def test_el_detalle_trae_los_mismos_campos(admin, datos):
    cuerpo = admin.get(f"/api/sites/{datos['torre'].id}").json()
    assert cuerpo["sensor_count"] == 2
    assert cuerpo["status"] == "CRITICAL"


def test_un_cliente_tambien_ve_estado_y_sensores_de_los_suyos(client, datos):
    _entrar(client, datos["cliente"])
    sites = _por_nombre(client.get("/api/sites").json())
    assert set(sites) == {"Torre", "Anexo", "Vacío"}
    assert sites["Torre"]["status"] == "CRITICAL"


def test_los_campos_calculados_no_hacen_una_consulta_por_site(engine, datos):
    def consultas():
        cuenta = [0]

        def contar(*_):
            cuenta[0] += 1

        event.listen(engine, "before_cursor_execute", contar)
        with Session(engine) as db:
            SiteService(db).list(organization_id=None, offset=0, limit=50)
        event.remove(engine, "before_cursor_execute", contar)
        return cuenta[0]

    antes = consultas()
    with Session(engine) as db:
        db.add_all([Site(organization_id=datos["luna"].id, name=f"Extra {i}")
                    for i in range(10)])
        db.commit()
    assert consultas() == antes


# ---------------------------------------------------------
# PERMISOS DE LAS RUTAS NUEVAS
# ---------------------------------------------------------
@pytest.mark.parametrize(
    ("metodo", "ruta"),
    [("post", "/api/sites"), ("patch", "/api/sites/{id}"), ("delete", "/api/sites/{id}")],
)
def test_un_cliente_no_puede_crear_editar_ni_borrar(client, datos, metodo, ruta):
    _entrar(client, datos["cliente"])
    url = ruta.format(id=datos["vacio"].id)
    kwargs = {"json": {"name": "X", "organization_id": str(datos["sol"].id)}} if metodo != "delete" else {}

    assert getattr(client, metodo)(url, **kwargs).status_code == 403


# ---------------------------------------------------------
# ALTA
# ---------------------------------------------------------
def test_alta_de_un_edificio(admin, datos):
    respuesta = admin.post("/api/sites", json={
        "organization_id": str(datos["luna"].id),
        "name": "Gimnasio",
        "latitude": 41.38,
        "longitude": 2.17,
        "floors": 2,
        "basements": 1,
        "building_type": "SPORTS",
    })

    cuerpo = respuesta.json()
    assert respuesta.status_code == 201
    assert cuerpo["organization_name"] == "Colegio Luna"
    assert (cuerpo["floors"], cuerpo["basements"], cuerpo["building_type"]) == (2, 1, "SPORTS")
    assert (cuerpo["sensor_count"], cuerpo["status"]) == (0, "OK")
    assert cuerpo["latitude"] == 41.38


def test_alta_con_valores_por_defecto(admin, datos):
    cuerpo = admin.post("/api/sites", json={
        "organization_id": str(datos["luna"].id), "name": "Caseta",
    }).json()
    assert (cuerpo["floors"], cuerpo["basements"], cuerpo["building_type"]) == (1, 0, "OTHER")


def test_alta_en_un_cliente_que_no_existe_da_404(admin, datos):
    respuesta = admin.post("/api/sites", json={
        "organization_id": "00000000-0000-4000-8000-000000000000", "name": "X",
    })
    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "ORGANIZATION_NOT_FOUND"


def test_nombre_repetido_en_el_mismo_cliente_da_409(admin, datos):
    respuesta = admin.post("/api/sites", json={
        "organization_id": str(datos["sol"].id), "name": "Torre",
    })
    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "SITE_NAME_TAKEN"


def test_el_mismo_nombre_en_otro_cliente_es_valido(admin, datos):
    respuesta = admin.post("/api/sites", json={
        "organization_id": str(datos["luna"].id), "name": "Torre",
    })
    assert respuesta.status_code == 201


@pytest.mark.parametrize(
    "cambio",
    [
        {"floors": 0},
        {"basements": -1},
        {"floors": 201},
        {"building_type": "CASTILLO"},
        {"latitude": 91},
        {"name": ""},
    ],
)
def test_datos_invalidos_en_el_alta_dan_422(admin, datos, cambio):
    cuerpo = {"organization_id": str(datos["luna"].id), "name": "Nuevo", **cambio}
    assert admin.post("/api/sites", json=cuerpo).status_code == 422


def test_el_primer_edificio_del_alta_de_organizacion_guarda_plantas_y_tipo(admin, engine, datos):
    """El `first_site` de la B1 usa los mismos campos que el alta de site."""
    respuesta = admin.post("/api/organizations", json={
        "name": "Residencia Mar",
        "phone": "612 345 678",
        "first_site": {"name": "Edificio A", "floors": 4, "basements": 1,
                       "building_type": "RESIDENCE"},
    })
    assert respuesta.status_code == 201
    with Session(engine) as db:
        site = db.scalar(select(Site).where(Site.name == "Edificio A"))
        assert (site.floors, site.basements, site.building_type) == (4, 1, "RESIDENCE")


# ---------------------------------------------------------
# EDICIÓN
# ---------------------------------------------------------
def test_editar_solo_cambia_lo_enviado(admin, datos):
    cuerpo = admin.patch(f"/api/sites/{datos['torre'].id}",
                         json={"floors": 8, "building_type": "OFFICE"}).json()

    assert (cuerpo["floors"], cuerpo["building_type"]) == (8, "OFFICE")
    assert cuerpo["basements"] == 2
    assert cuerpo["name"] == "Torre"


def test_quitar_plantas_con_sensores_da_422(admin, datos):
    """Hay un sensor en la planta 5: con 5 plantas la más alta es la 4."""
    respuesta = admin.patch(f"/api/sites/{datos['torre'].id}", json={"floors": 5})

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "FLOOR_OUT_OF_SITE"


def test_quitar_sotanos_con_sensores_da_422(admin, datos):
    """Hay un sensor en la planta -2."""
    respuesta = admin.patch(f"/api/sites/{datos['torre'].id}", json={"basements": 1})

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "FLOOR_OUT_OF_SITE"


def test_quitar_plantas_sin_sensores_en_ellas_es_valido(admin, datos):
    """Con 6 plantas exactas el sensor de la planta 5 sigue dentro."""
    respuesta = admin.patch(f"/api/sites/{datos['torre'].id}",
                            json={"floors": 6, "basements": 2})
    assert respuesta.status_code == 200


def test_renombrar_con_el_nombre_de_otro_edificio_del_cliente_da_409(admin, datos):
    respuesta = admin.patch(f"/api/sites/{datos['anexo'].id}", json={"name": "Torre"})
    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "SITE_NAME_TAKEN"


@pytest.mark.parametrize("campo", ["name", "floors", "basements", "building_type"])
def test_dejar_vacio_un_campo_obligatorio_da_422(admin, datos, campo):
    respuesta = admin.patch(f"/api/sites/{datos['vacio'].id}", json={campo: None})
    assert respuesta.status_code == 422


def test_no_se_puede_cambiar_de_cliente(admin, datos):
    respuesta = admin.patch(f"/api/sites/{datos['vacio'].id}",
                            json={"organization_id": str(datos["luna"].id)})
    assert respuesta.status_code == 422


def test_editar_un_site_que_no_existe_da_404(admin, datos):
    respuesta = admin.patch("/api/sites/00000000-0000-4000-8000-000000000000",
                            json={"name": "X"})
    assert respuesta.status_code == 404


# ---------------------------------------------------------
# BORRADO
# ---------------------------------------------------------
def test_borrar_un_edificio_sin_sensores(admin, datos):
    respuesta = admin.delete(f"/api/sites/{datos['vacio'].id}")

    assert respuesta.status_code == 204
    assert admin.get(f"/api/sites/{datos['vacio'].id}").status_code == 404


def test_borrar_un_edificio_con_sensores_da_409(admin, datos):
    respuesta = admin.delete(f"/api/sites/{datos['torre'].id}")

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "SITE_HAS_SENSORS"
    assert admin.get(f"/api/sites/{datos['torre'].id}").status_code == 200


def test_borrar_un_edificio_con_documentos_da_409_y_no_los_borra(admin, datos, engine):
    """
    `documents.site_id` es ON DELETE CASCADE: sin esta comprobación, borrar
    el edificio se llevaría sus documentos sin avisar (revisión de la #194).
    """
    with Session(engine) as s:
        s.add(Document(organization_id=datos["sol"].id, site_id=datos["vacio"].id,
                       kind="PLAN", filename="plano.pdf",
                       content_type="application/pdf", size=1024,
                       storage_key="sol/vacio/plano.pdf"))
        s.commit()

    respuesta = admin.delete(f"/api/sites/{datos['vacio'].id}")

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "SITE_HAS_DOCUMENTS"
    assert admin.get(f"/api/sites/{datos['vacio'].id}").status_code == 200
    with Session(engine) as s:
        assert s.scalar(select(Document.filename)) == "plano.pdf"


def test_borrar_un_site_que_no_existe_da_404(admin, datos):
    respuesta = admin.delete("/api/sites/00000000-0000-4000-8000-000000000000")
    assert respuesta.status_code == 404
