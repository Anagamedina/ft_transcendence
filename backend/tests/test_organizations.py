"""
Organizaciones (B1, issue #139; incluye la #121).

Cubre las 8 rutas, sus errores, los contadores, los cambios de estado y la
regla que más importa: una organización suspendida deja fuera a sus
usuarios, también a los que ya tenían la sesión abierta.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.app_config import app_settings
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token, hash_password
from app.main import app
from app.modules.alerts.model import Alert
from app.modules.organizations.model import Organization
from app.modules.organizations.service import OrganizationService
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User

PASSWORD = "una-contraseña-larga"


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
    Hotel Sol: 2 edificios, 3 sensores, 1 usuario y 3 alertas abiertas (1
    crítica) más una resuelta. Colegio Luna: vacío, en prueba.
    """
    with Session(engine, expire_on_commit=False) as s:
        sol = Organization(name="Hotel Sol", city="Barcelona", tax_id="B11111111")
        luna = Organization(
            name="Colegio Luna",
            status="TRIAL",
            trial_ends_at=datetime.now(timezone.utc) + timedelta(days=3),
        )
        s.add_all([sol, luna])
        s.flush()

        torre = Site(organization_id=sol.id, name="Torre")
        anexo = Site(organization_id=sol.id, name="Anexo")
        s.add_all([torre, anexo])
        s.flush()

        sensores = [
            Sensor(
                site_id=site.id,
                external_id=f"S-{i}",
                name=f"Sensor {i}",
                unit="bar",
                low_threshold=Decimal("1"),
                high_threshold=Decimal("9"),
            )
            for i, site in enumerate([torre, torre, anexo])
        ]
        s.add_all(sensores)
        s.flush()

        for severidad, estado in [
            ("WARNING", "ACTIVE"),
            ("WARNING", "ACTIVE"),
            ("CRITICAL", "ACTIVE"),
            ("CRITICAL", "RESOLVED"),
        ]:
            s.add(
                Alert(
                    sensor_id=sensores[0].id,
                    alert_type="LOW_PRESSURE",
                    severity=severidad,
                    message="Presión baja",
                    status=estado,
                )
            )

        cliente = User(
            organization_id=sol.id,
            email="cliente@sol.dev",
            name="Cliente Sol",
            password_hash=hash_password(PASSWORD),
            role="client",
        )
        admin = User(
            email="admin@aquaguard.dev",
            name="Admin",
            password_hash=hash_password(PASSWORD),
            role="admin",
        )
        s.add_all([cliente, admin])
        s.commit()
        return {"sol": sol, "luna": luna, "cliente": cliente, "admin": admin}


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


# ---------------------------------------------------------
# PERMISOS
# ---------------------------------------------------------
RUTAS = [
    ("get", "/api/organizations"),
    ("post", "/api/organizations"),
    ("get", "/api/organizations/{id}"),
    ("patch", "/api/organizations/{id}"),
    ("post", "/api/organizations/{id}/suspend"),
    ("post", "/api/organizations/{id}/reactivate"),
    ("post", "/api/organizations/{id}/extend-trial"),
    ("post", "/api/organizations/{id}/activate"),
]


@pytest.mark.parametrize(("metodo", "ruta"), RUTAS)
def test_sin_sesion_da_401(client, datos, metodo, ruta):
    respuesta = getattr(client, metodo)(ruta.format(id=datos["sol"].id))
    assert respuesta.status_code == 401


@pytest.mark.parametrize(("metodo", "ruta"), RUTAS)
def test_un_cliente_recibe_403(client, datos, metodo, ruta):
    _entrar(client, datos["cliente"])
    respuesta = getattr(client, metodo)(ruta.format(id=datos["sol"].id))
    assert respuesta.status_code == 403


# ---------------------------------------------------------
# LISTAR Y VER
# ---------------------------------------------------------
def test_lista_por_nombre_con_contadores(admin, datos):
    cuerpo = admin.get("/api/organizations").json()

    assert [o["name"] for o in cuerpo["items"]] == ["Colegio Luna", "Hotel Sol"]
    sol = cuerpo["items"][1]
    assert sol["site_count"] == 2
    assert sol["sensor_count"] == 3
    assert sol["user_count"] == 1
    assert sol["open_alerts"] == 3  # la resuelta no cuenta
    assert sol["critical_alerts"] == 1
    luna = cuerpo["items"][0]
    assert (luna["site_count"], luna["open_alerts"]) == (0, 0)


@pytest.mark.parametrize(
    ("params", "esperado"),
    [
        ({"status": "TRIAL"}, ["Colegio Luna"]),
        ({"has_open_alerts": "true"}, ["Hotel Sol"]),
        ({"has_open_alerts": "false"}, ["Colegio Luna"]),
        ({"q": "barcelona"}, ["Hotel Sol"]),  # ciudad
        ({"q": "b1111"}, ["Hotel Sol"]),  # NIF
        ({"q": "luna"}, ["Colegio Luna"]),
    ],
)
def test_filtros_del_listado(admin, datos, params, esperado):
    cuerpo = admin.get("/api/organizations", params=params).json()
    assert [o["name"] for o in cuerpo["items"]] == esperado


def test_los_contadores_no_hacen_una_consulta_por_organizacion(engine, datos):
    """Con 2 o con 12 organizaciones, las mismas consultas."""
    from sqlalchemy import event

    def consultas_de_listar():
        cuenta = [0]

        def contar(*_):
            cuenta[0] += 1

        event.listen(engine, "before_cursor_execute", contar)
        with Session(engine) as db:
            OrganizationService(db).list(offset=0, limit=50)
        event.remove(engine, "before_cursor_execute", contar)
        return cuenta[0]

    con_dos = consultas_de_listar()
    with Session(engine) as db:
        db.add_all([Organization(name=f"Extra {i}") for i in range(10)])
        db.commit()
    assert consultas_de_listar() == con_dos


def test_ver_una_organizacion(admin, datos):
    cuerpo = admin.get(f"/api/organizations/{datos['sol'].id}").json()
    assert cuerpo["name"] == "Hotel Sol"
    assert cuerpo["status"] == "ACTIVE"
    assert cuerpo["site_count"] == 2


def test_ver_una_que_no_existe_da_404(admin, datos):
    respuesta = admin.get("/api/organizations/00000000-0000-4000-8000-000000000000")
    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "ORGANIZATION_NOT_FOUND"


# ---------------------------------------------------------
# ALTA (incluye los criterios de la #121)
# ---------------------------------------------------------
def test_alta_y_aparece_en_la_lista(admin, datos):
    respuesta = admin.post("/api/organizations", json={"name": "Residencia Mar"})

    assert respuesta.status_code == 201
    assert respuesta.json()["status"] == "ACTIVE"
    nombres = [o["name"] for o in admin.get("/api/organizations").json()["items"]]
    assert "Residencia Mar" in nombres


def test_alta_con_primer_edificio(admin, engine, datos):
    respuesta = admin.post(
        "/api/organizations",
        json={
            "name": "Residencia Mar",
            "city": "Sitges",
            "contact_email": "info@mar.dev",
            "first_site": {"name": "Edificio A", "latitude": 41.23, "longitude": 1.8},
        },
    )

    cuerpo = respuesta.json()
    assert respuesta.status_code == 201
    assert cuerpo["site_count"] == 1
    assert cuerpo["city"] == "Sitges"
    with Session(engine) as db:
        site = db.scalar(select(Site).where(Site.name == "Edificio A"))
        assert str(site.organization_id) == cuerpo["id"]


def test_si_el_primer_edificio_falla_no_queda_la_organizacion(admin, engine, datos):
    respuesta = admin.post(
        "/api/organizations",
        json={"name": "Residencia Mar", "first_site": {"name": "A", "latitude": 200}},
    )

    assert respuesta.status_code == 422
    with Session(engine) as db:
        assert db.scalar(
            select(func.count()).where(Organization.name == "Residencia Mar")
        ) == 0


@pytest.mark.parametrize("nombre", ["Hotel Sol", "hotel sol", "  HOTEL SOL  "])
def test_nombre_repetido_sin_distinguir_mayusculas_da_409(admin, datos, nombre):
    respuesta = admin.post("/api/organizations", json={"name": nombre})
    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "ORGANIZATION_NAME_TAKEN"


@pytest.mark.parametrize("nombre", ["", "   "])
def test_nombre_vacio_da_422_invalid_name(admin, datos, nombre):
    respuesta = admin.post("/api/organizations", json={"name": nombre})
    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "INVALID_NAME"


def test_un_nombre_de_120_caracteres_se_guarda(admin, datos):
    respuesta = admin.post("/api/organizations", json={"name": "x" * 120})
    assert respuesta.status_code == 201


def test_un_nombre_de_121_caracteres_da_422(admin, datos):
    respuesta = admin.post("/api/organizations", json={"name": "x" * 121})
    assert respuesta.status_code == 422


def test_email_de_contacto_mal_escrito_da_422(admin, datos):
    respuesta = admin.post(
        "/api/organizations", json={"name": "Nueva", "contact_email": "no-es-un-email"}
    )
    assert respuesta.status_code == 422


def test_un_cliente_dado_de_alta_en_la_nueva_organizacion_no_ve_nada_ajeno(
    admin, client, datos
):
    """Criterio de la #121: el cliente de la organización nueva empieza vacío."""
    org = admin.post("/api/organizations", json={"name": "Residencia Mar"}).json()
    alta = admin.post(
        "/api/auth/register",
        json={
            "name": "Recepción Mar",
            "email": "recepcion@mar.dev",
            "password": PASSWORD,
            "organization_id": org["id"],
        },
    )
    assert alta.status_code == 201

    client.cookies.clear()
    assert client.post(
        "/api/auth/login", json={"email": "recepcion@mar.dev", "password": PASSWORD}
    ).status_code == 200
    assert client.get("/api/sites").json()["total"] == 0
    assert client.get("/api/sensors").json()["total"] == 0
    assert client.get("/api/alerts").json()["total"] == 0


# ---------------------------------------------------------
# EDITAR
# ---------------------------------------------------------
def test_editar_solo_cambia_lo_enviado(admin, datos):
    respuesta = admin.patch(
        f"/api/organizations/{datos['sol'].id}",
        json={"phone": "+34 600 000 000", "legal_name": "Hoteles Sol S.L."},
    )

    cuerpo = respuesta.json()
    assert respuesta.status_code == 200
    assert cuerpo["phone"] == "+34 600 000 000"
    assert cuerpo["legal_name"] == "Hoteles Sol S.L."
    assert cuerpo["city"] == "Barcelona"  # no se envió: se conserva
    assert cuerpo["name"] == "Hotel Sol"


def test_renombrar_con_el_mismo_nombre_en_otras_mayusculas_es_valido(admin, datos):
    respuesta = admin.patch(
        f"/api/organizations/{datos['sol'].id}", json={"name": "HOTEL SOL"}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["name"] == "HOTEL SOL"


def test_renombrar_con_el_nombre_de_otra_da_409(admin, datos):
    respuesta = admin.patch(
        f"/api/organizations/{datos['sol'].id}", json={"name": "colegio luna"}
    )
    assert respuesta.status_code == 409


@pytest.mark.parametrize("nombre", [None, "  "])
def test_renombrar_a_vacio_da_422(admin, datos, nombre):
    respuesta = admin.patch(
        f"/api/organizations/{datos['sol'].id}", json={"name": nombre}
    )
    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "INVALID_NAME"


def test_el_estado_no_se_cambia_con_patch(admin, datos):
    respuesta = admin.patch(
        f"/api/organizations/{datos['sol'].id}", json={"status": "SUSPENDED"}
    )
    assert respuesta.status_code == 422


# ---------------------------------------------------------
# CAMBIOS DE ESTADO
# ---------------------------------------------------------
def test_suspender_y_reactivar_un_cliente(admin, datos):
    url = f"/api/organizations/{datos['sol'].id}"

    assert admin.post(f"{url}/suspend").json()["status"] == "SUSPENDED"
    assert admin.post(f"{url}/reactivate").json()["status"] == "ACTIVE"


def test_reactivar_una_prueba_la_devuelve_a_trial(admin, datos):
    url = f"/api/organizations/{datos['luna'].id}"

    admin.post(f"{url}/suspend")
    cuerpo = admin.post(f"{url}/reactivate").json()

    assert cuerpo["status"] == "TRIAL"
    assert cuerpo["trial_ends_at"] is not None


def test_suspender_dos_veces_da_409(admin, datos):
    url = f"/api/organizations/{datos['sol'].id}"
    admin.post(f"{url}/suspend")

    respuesta = admin.post(f"{url}/suspend")

    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "ORGANIZATION_ALREADY_SUSPENDED"


def test_reactivar_una_que_no_esta_suspendida_da_409(admin, datos):
    respuesta = admin.post(f"/api/organizations/{datos['sol'].id}/reactivate")
    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "ORGANIZATION_NOT_SUSPENDED"


def test_activar_una_prueba(admin, datos):
    cuerpo = admin.post(f"/api/organizations/{datos['luna'].id}/activate").json()
    assert cuerpo["status"] == "ACTIVE"
    assert cuerpo["trial_ends_at"] is None


@pytest.mark.parametrize("accion", ["activate", "extend-trial"])
def test_activar_o_ampliar_algo_que_no_es_prueba_da_409(admin, datos, accion):
    respuesta = admin.post(f"/api/organizations/{datos['sol'].id}/{accion}")
    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "ORGANIZATION_NOT_IN_TRIAL"


def test_ampliar_suma_los_dias_al_fin_actual(admin, datos):
    fin = datetime.fromisoformat(
        admin.get(f"/api/organizations/{datos['luna'].id}").json()["trial_ends_at"]
    )

    cuerpo = admin.post(f"/api/organizations/{datos['luna'].id}/extend-trial").json()

    nuevo = datetime.fromisoformat(cuerpo["trial_ends_at"])
    assert nuevo - fin == timedelta(days=app_settings.TRIAL_DAYS)


def test_ampliar_una_prueba_caducada_cuenta_desde_hoy(engine, datos):
    ahora = datetime(2026, 10, 10, 12, 0, tzinfo=timezone.utc)
    with Session(engine, expire_on_commit=False) as db:
        org = db.get(Organization, datos["luna"].id)
        org.trial_ends_at = ahora - timedelta(days=30)
        db.commit()

        cuerpo = OrganizationService(db).extend_trial(org.id, ahora=ahora)

    assert cuerpo.trial_ends_at == ahora + timedelta(days=app_settings.TRIAL_DAYS)


# ---------------------------------------------------------
# UNA ORGANIZACIÓN SUSPENDIDA DEJA FUERA A SUS USUARIOS
# ---------------------------------------------------------
def test_un_usuario_de_una_organizacion_suspendida_no_puede_hacer_login(
    admin, client, datos
):
    admin.post(f"/api/organizations/{datos['sol'].id}/suspend")
    client.cookies.clear()

    respuesta = client.post(
        "/api/auth/login", json={"email": "cliente@sol.dev", "password": PASSWORD}
    )

    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "ACCOUNT_DISABLED"


def test_con_la_contrasena_mal_no_se_revela_que_esta_suspendida(admin, client, datos):
    admin.post(f"/api/organizations/{datos['sol'].id}/suspend")
    client.cookies.clear()

    respuesta = client.post(
        "/api/auth/login", json={"email": "cliente@sol.dev", "password": "otra-cosa-larga"}
    )

    assert respuesta.status_code == 401


def test_una_sesion_ya_abierta_deja_de_servir_al_suspender(admin, engine, datos):
    # Otro navegador: sin `with`, para no arrancar la tarea de fondo.
    cliente = TestClient(app)
    _entrar(cliente, datos["cliente"])
    assert cliente.get("/api/me").status_code == 200

    admin.post(f"/api/organizations/{datos['sol'].id}/suspend")

    respuesta = cliente.get("/api/me")
    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "ACCOUNT_DISABLED"


def test_al_reactivar_vuelve_a_poder_entrar(admin, client, datos):
    url = f"/api/organizations/{datos['sol'].id}"
    admin.post(f"{url}/suspend")
    admin.post(f"{url}/reactivate")
    client.cookies.clear()

    respuesta = client.post(
        "/api/auth/login", json={"email": "cliente@sol.dev", "password": PASSWORD}
    )

    assert respuesta.status_code == 200


def test_el_admin_no_se_bloquea_aunque_su_organizacion_este_suspendida(
    engine, client, datos
):
    with Session(engine, expire_on_commit=False) as db:
        db.get(User, datos["admin"].id).organization_id = datos["sol"].id
        db.get(Organization, datos["sol"].id).status = "SUSPENDED"
        db.commit()

    respuesta = client.post(
        "/api/auth/login", json={"email": "admin@aquaguard.dev", "password": PASSWORD}
    )

    assert respuesta.status_code == 200
