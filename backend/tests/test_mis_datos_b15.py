"""
Exportar mis datos y pedir la baja (B15, issue #149).

Criterio de la issue: el usuario puede exportar sus datos y pedir la baja.

Más lo que no puede fallar en una exportación de datos personales: que
solo salga lo de quien la pide (nunca los edificios de otra organización,
tampoco para un admin sin organización) y que no salga la contraseña.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.app_config import app_settings
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token, hash_password
from app.main import app
from app.modules.organizations.model import Organization
from app.modules.sites.model import Site
from app.modules.users.model import User
from app.modules.users.service import UserService

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
    Hotel Mar (con dos edificios y su cliente) y Colegio Luna (con uno),
    más un admin sin organización.
    """
    with Session(engine, expire_on_commit=False) as s:
        mar = Organization(
            name="Hotel Mar",
            status="ACTIVE",
            city="Barcelona",
            tax_id="B12345678",
            plan="PRO",
            iban_masked="ES** **** **** **** **** 1332",
        )
        luna = Organization(name="Colegio Luna")
        s.add_all([mar, luna])
        s.flush()

        s.add_all(
            [
                Site(
                    organization_id=mar.id,
                    name="Torre",
                    address="Avinguda Diagonal 100",
                    latitude=Decimal("41.4036"),
                    longitude=Decimal("2.2144"),
                    district="SANT_MARTI",
                    floors=12,
                    basements=2,
                    building_type="HOTEL",
                ),
                Site(organization_id=mar.id, name="Anexo"),
                Site(organization_id=luna.id, name="Gimnasio"),
            ]
        )

        cliente = User(
            organization_id=mar.id,
            email="ana@hotelmar.dev",
            name="Ana Medina",
            password_hash=hash_password(PASSWORD),
            role="client",
            terms_version="2026-10",
            terms_accepted_at=datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc),
        )
        admin = User(
            email="admin@aquaguard.dev",
            name="Admin",
            password_hash=hash_password(PASSWORD),
            role="admin",
        )
        s.add_all([cliente, admin])
        s.commit()
        return {"mar": mar, "luna": luna, "cliente": cliente, "admin": admin}


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
    return client


@pytest.fixture()
def cliente(client, datos):
    return _entrar(client, datos["cliente"])


def _usuario(engine, user_id):
    with Session(engine) as s:
        return s.get(User, user_id)


def _fecha(valor):
    """Fecha de la respuesta en UTC. sqlite (tests) la devuelve sin zona."""
    fecha = datetime.fromisoformat(valor.replace("Z", "+00:00"))
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


def _utc(fecha):
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------
# GET /api/me/export
# ---------------------------------------------------------
def test_sin_sesion_no_se_exporta(client):
    respuesta = client.get("/api/me/export")

    assert respuesta.status_code == 401
    assert respuesta.json()["error"]["code"] == "UNAUTHORIZED"


def test_exporta_la_cuenta_con_los_terminos(cliente, datos):
    respuesta = cliente.get("/api/me/export")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    cuenta = cuerpo["account"]
    assert cuenta["email"] == "ana@hotelmar.dev"
    assert cuenta["name"] == "Ana Medina"
    assert cuenta["role"] == "client"
    assert cuenta["terms_version"] == "2026-10"
    assert _fecha(cuenta["terms_accepted_at"]) == datetime(
        2026, 10, 1, 10, 0, tzinfo=timezone.utc
    )
    assert cuenta["deletion_requested_at"] is None
    assert cuerpo["current_terms_version"] == app_settings.TERMS_VERSION


def test_se_descarga_como_archivo_y_no_se_cachea(cliente):
    respuesta = cliente.get("/api/me/export")

    disposicion = respuesta.headers["content-disposition"]
    assert disposicion.startswith('attachment; filename="aquaguard-mis-datos_')
    assert disposicion.endswith('.json"')
    assert respuesta.headers["cache-control"] == "no-store"


def test_no_sale_la_contrasena(cliente):
    texto = cliente.get("/api/me/export").text

    assert "password" not in texto
    assert "argon2" not in texto


def test_exporta_la_organizacion_con_el_iban_solo_enmascarado(cliente):
    organizacion = cliente.get("/api/me/export").json()["organization"]

    assert organizacion["name"] == "Hotel Mar"
    assert organizacion["status"] == "ACTIVE"
    assert organizacion["tax_id"] == "B12345678"
    assert organizacion["plan"] == "PRO"
    assert organizacion["iban_masked"] == "ES** **** **** **** **** 1332"
    assert "iban" not in organizacion


def test_exporta_solo_los_edificios_de_su_organizacion(cliente):
    sitios = cliente.get("/api/me/export").json()["sites"]

    # Por nombre, y sin el Gimnasio de Colegio Luna.
    assert [s["name"] for s in sitios] == ["Anexo", "Torre"]
    torre = sitios[1]
    assert torre["address"] == "Avinguda Diagonal 100"
    assert torre["latitude"] == pytest.approx(41.4036)
    assert torre["district"] == "SANT_MARTI"
    assert torre["floors"] == 12
    assert torre["basements"] == 2
    assert torre["building_type"] == "HOTEL"


def test_un_admin_sin_organizacion_no_exporta_los_edificios_de_todos(client, datos):
    admin = _entrar(client, datos["admin"])

    cuerpo = admin.get("/api/me/export").json()

    assert cuerpo["account"]["role"] == "admin"
    assert cuerpo["organization"] is None
    assert cuerpo["sites"] == []


# ---------------------------------------------------------
# POST /api/me/deletion-request
# ---------------------------------------------------------
def test_sin_sesion_no_se_pide_la_baja(client):
    respuesta = client.post("/api/me/deletion-request")

    assert respuesta.status_code == 401


def test_pedir_la_baja_la_registra(cliente, datos, engine):
    respuesta = cliente.post("/api/me/deletion-request")

    assert respuesta.status_code == 202
    cuerpo = respuesta.json()
    assert cuerpo["message"]
    guardada = _usuario(engine, datos["cliente"].id).deletion_requested_at
    assert guardada is not None
    assert _fecha(cuerpo["deletion_requested_at"]) == _utc(guardada)


def test_la_baja_pedida_sale_en_me_y_en_la_exportacion(cliente):
    cliente.post("/api/me/deletion-request")

    assert cliente.get("/api/me").json()["deletion_requested_at"] is not None
    cuenta = cliente.get("/api/me/export").json()["account"]
    assert cuenta["deletion_requested_at"] is not None


def test_pedirla_otra_vez_no_cambia_la_fecha(engine, datos):
    primera = datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)
    with Session(engine, expire_on_commit=False) as db:
        usuario = db.get(User, datos["cliente"].id)
        UserService(db).request_deletion(usuario, ahora=primera)

        otra = UserService(db).request_deletion(
            usuario, ahora=primera + timedelta(days=1)
        )

    assert _utc(otra.deletion_requested_at) == primera


def test_pedir_la_baja_no_borra_nada(cliente, client, datos, engine):
    cliente.post("/api/me/deletion-request")
    client.cookies.clear()

    with Session(engine) as s:
        assert s.get(Organization, datos["mar"].id) is not None
        assert s.query(Site).filter_by(organization_id=datos["mar"].id).count() == 2
    # Y sigue pudiendo entrar y descargar sus datos hasta que la tramiten.
    entrada = client.post(
        "/api/auth/login", json={"email": "ana@hotelmar.dev", "password": PASSWORD}
    )
    assert entrada.status_code == 200
    assert client.get("/api/me/export").status_code == 200


def test_con_la_prueba_vencida_tambien_se_puede_pedir_la_baja(cliente, datos, engine):
    with Session(engine) as s:
        org = s.get(Organization, datos["mar"].id)
        org.status = "TRIAL"
        org.trial_ends_at = datetime.now(timezone.utc) - timedelta(days=1)
        s.commit()

    assert cliente.get("/api/me/export").status_code == 200
    assert cliente.post("/api/me/deletion-request").status_code == 202


# ---------------------------------------------------------
# OPENAPI
# ---------------------------------------------------------
@pytest.mark.parametrize("nombre", ["MyDataExport", "DeletionRequestResponse"])
def test_openapi_publica_el_contrato_con_ejemplo(nombre):
    schemas = app.openapi()["components"]["schemas"]

    assert schemas[nombre].get("examples"), nombre
