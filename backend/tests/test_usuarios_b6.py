"""
Gestión de usuarios del admin (B6, issue #141).

Lo que más importa: el admin lista, edita (también el rol), activa,
desactiva y quita usuarios; el email no se edita; un usuario inactivo no
entra, y un admin no puede dejarse fuera a sí mismo.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token, hash_password
from app.main import app
from app.modules.organizations.model import Organization
from app.modules.users.model import User

PASSWORD = "agua-que-no-se-escapa"


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
    huella = hash_password(PASSWORD)
    with Session(engine, expire_on_commit=False) as s:
        hotel = Organization(name="Hotel Mar")
        colegio = Organization(name="Colegio Luna")
        s.add_all([hotel, colegio])
        s.flush()
        usuarios = {
            "admin": User(email="admin@aquaguard.dev", name="Ana", password_hash=huella,
                          role="admin", is_active=True),
            "otro_admin": User(email="otro@aquaguard.dev", name="Bea", password_hash=huella,
                               role="admin", is_active=True),
            "laura": User(organization_id=hotel.id, email="laura@hotelmar.dev",
                          name="Laura Puig", password_hash=huella, role="client", is_active=True),
            "pau": User(organization_id=colegio.id, email="pau@luna.dev", name="Pau",
                        password_hash=huella, role="client", is_active=False),
        }
        s.add_all(usuarios.values())
        s.commit()
        return {"hotel": hotel, "colegio": colegio, **usuarios}


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


def _codigo(respuesta):
    return respuesta.json()["error"]["code"]


def _login(client, email):
    return client.post("/api/auth/login", json={"email": email, "password": PASSWORD})


# ---------------------------------------------------------
# LISTAR Y VER
# ---------------------------------------------------------
def test_un_cliente_no_gestiona_usuarios(client, datos):
    _entrar(client, datos["laura"])
    assert client.get("/api/users").status_code == 403
    assert client.post(f"/api/users/{datos['pau'].id}/activate").status_code == 403


def test_el_admin_lista_con_filtros(client, datos):
    _entrar(client, datos["admin"])

    todos = client.get("/api/users").json()
    assert todos["total"] == 4
    laura = next(u for u in todos["items"] if u["email"] == "laura@hotelmar.dev")
    assert laura["organization_name"] == "Hotel Mar"
    assert laura["is_active"] is True
    assert "password_hash" not in laura

    def emails(url):
        return [u["email"] for u in client.get(url).json()["items"]]

    assert emails(f"/api/users?organization_id={datos['hotel'].id}") == ["laura@hotelmar.dev"]
    assert emails("/api/users?q=LUNA") == ["pau@luna.dev"]
    assert emails("/api/users?active=false") == ["pau@luna.dev"]
    assert len(emails("/api/users?active=true")) == 3


def test_ver_un_usuario(client, datos):
    _entrar(client, datos["admin"])
    assert client.get(f"/api/users/{datos['laura'].id}").json()["name"] == "Laura Puig"

    respuesta = client.get("/api/users/11111111-1111-4111-8111-111111111111")
    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "USER_NOT_FOUND"


# ---------------------------------------------------------
# EDITAR
# ---------------------------------------------------------
def test_editar_nombre_rol_y_organizacion(client, datos):
    _entrar(client, datos["admin"])

    respuesta = client.patch(
        f"/api/users/{datos['laura'].id}",
        json={"name": " Laura P. ", "organization_id": str(datos["colegio"].id)},
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["name"] == "Laura P."
    assert respuesta.json()["organization_name"] == "Colegio Luna"

    ascendida = client.patch(f"/api/users/{datos['laura'].id}", json={"role": "admin"})
    assert ascendida.json()["role"] == "admin"


def test_el_email_no_se_edita(client, datos):
    _entrar(client, datos["admin"])
    respuesta = client.patch(
        f"/api/users/{datos['laura'].id}", json={"email": "nuevo@hotelmar.dev"}
    )
    assert respuesta.status_code == 422


def test_un_cliente_no_puede_quedar_sin_organizacion(client, datos):
    _entrar(client, datos["admin"])
    respuesta = client.patch(
        f"/api/users/{datos['laura'].id}", json={"organization_id": None}
    )
    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "ORGANIZATION_REQUIRED"


def test_a_admin_y_sin_organizacion_en_la_misma_peticion(client, datos):
    _entrar(client, datos["admin"])
    respuesta = client.patch(
        f"/api/users/{datos['laura'].id}", json={"role": "admin", "organization_id": None}
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["organization_id"] is None


def test_organizacion_inexistente_da_404(client, datos):
    _entrar(client, datos["admin"])
    respuesta = client.patch(
        f"/api/users/{datos['laura'].id}",
        json={"organization_id": "11111111-1111-4111-8111-111111111111"},
    )
    assert respuesta.status_code == 404
    assert _codigo(respuesta) == "ORGANIZATION_NOT_FOUND"


# ---------------------------------------------------------
# UN ADMIN NO SE DEJA FUERA A SÍ MISMO
# ---------------------------------------------------------
def test_un_admin_no_se_quita_su_rol(client, datos):
    _entrar(client, datos["admin"])
    respuesta = client.patch(
        f"/api/users/{datos['admin'].id}",
        json={"role": "client", "organization_id": str(datos["hotel"].id)},
    )
    assert respuesta.status_code == 409
    assert _codigo(respuesta) == "CANNOT_DEMOTE_SELF"


def test_un_admin_no_se_desactiva_ni_se_borra(client, datos):
    _entrar(client, datos["admin"])
    desactivar = client.post(f"/api/users/{datos['admin'].id}/deactivate")
    borrar = client.delete(f"/api/users/{datos['admin'].id}")
    assert (desactivar.status_code, _codigo(desactivar)) == (409, "CANNOT_DEACTIVATE_SELF")
    assert (borrar.status_code, _codigo(borrar)) == (409, "CANNOT_DELETE_SELF")


def test_un_admin_si_puede_desactivar_a_otro_admin(client, datos):
    _entrar(client, datos["admin"])
    respuesta = client.post(f"/api/users/{datos['otro_admin'].id}/deactivate")
    assert respuesta.status_code == 200
    client.cookies.clear()

    assert _codigo(_login(client, "otro@aquaguard.dev")) == "ACCOUNT_DISABLED"


# ---------------------------------------------------------
# ACTIVAR, DESACTIVAR Y QUITAR EL ACCESO
# ---------------------------------------------------------
def test_un_usuario_inactivo_no_puede_entrar(client, datos):
    respuesta = _login(client, "pau@luna.dev")
    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "ACCOUNT_DISABLED"


def test_desactivar_corta_la_sesion_abierta(client, datos):
    _entrar(client, datos["laura"])
    assert client.get("/api/me").status_code == 200

    _entrar(client, datos["admin"])
    assert client.post(f"/api/users/{datos['laura'].id}/deactivate").json()["is_active"] is False

    _entrar(client, datos["laura"])
    respuesta = client.get("/api/me")
    assert respuesta.status_code == 403
    assert _codigo(respuesta) == "ACCOUNT_DISABLED"


def test_activar_devuelve_el_acceso(client, datos):
    _entrar(client, datos["admin"])
    assert client.post(f"/api/users/{datos['pau'].id}/activate").json()["is_active"] is True
    client.cookies.clear()

    assert _login(client, "pau@luna.dev").status_code == 200


def test_quitar_el_acceso(client, datos):
    _entrar(client, datos["admin"])
    assert client.delete(f"/api/users/{datos['laura'].id}").status_code == 204
    assert client.get(f"/api/users/{datos['laura'].id}").status_code == 404
    client.cookies.clear()

    assert _login(client, "laura@hotelmar.dev").status_code == 401


# ---------------------------------------------------------
# ÚLTIMO ACCESO
# ---------------------------------------------------------
def test_last_login_at_se_actualiza_en_cada_login(client, datos, engine):
    assert _login(client, "laura@hotelmar.dev").status_code == 200
    with Session(engine) as s:
        primero = s.get(User, datos["laura"].id).last_login_at
    assert primero is not None

    assert _login(client, "laura@hotelmar.dev").status_code == 200
    with Session(engine) as s:
        segundo = s.get(User, datos["laura"].id).last_login_at
    assert segundo > primero

    _entrar(client, datos["admin"])
    ficha = client.get(f"/api/users/{datos['laura'].id}").json()
    assert ficha["last_login_at"] is not None
