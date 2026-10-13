"""
Documentos por edificio (B11, issue #147): subir, listar, descargar y
borrar, con el tipo decidido por el contenido y el alcance por organización.
"""

from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core import models  # noqa: F401 - registra los modelos ORM
from app.core.app_config import app_settings
from app.core.database import Base, get_db
from app.core.security import SESSION_COOKIE, create_session_token
from app.main import app
from app.modules.documents.model import Document
from app.modules.documents.service import clean_filename
from app.modules.organizations.model import Organization
from app.modules.sites.model import Site
from app.modules.users.model import User

PDF = b"%PDF-1.7\n1 0 obj\n<<>>\nendobj\n%%EOF\n"
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 32
CSV = "fecha;presión\n2026-10-01;3,2\n".encode()
EXE = b"MZ\x90\x00\x03\x00\x00\x00"


# ---------------------------------------------------------
# DATOS
# ---------------------------------------------------------
@pytest.fixture()
def carpeta(tmp_path, monkeypatch):
    monkeypatch.setattr(app_settings, "DOCUMENTS_DIR", str(tmp_path))
    return tmp_path


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
    with Session(engine, expire_on_commit=False) as s:
        sol = Organization(name="Hotel Sol")
        luna = Organization(name="Colegio Luna")
        s.add_all([sol, luna])
        s.flush()
        torre = Site(organization_id=sol.id, name="Torre")
        anexo = Site(organization_id=sol.id, name="Anexo")
        patio = Site(organization_id=luna.id, name="Patio")
        s.add_all([torre, anexo, patio])
        cliente = User(organization_id=sol.id, email="cliente@sol.dev", name="Cliente",
                       password_hash="x", role="client")
        ajeno = User(organization_id=luna.id, email="cliente@luna.dev", name="Ajeno",
                     password_hash="x", role="client")
        admin = User(email="admin@aquaguard.dev", name="Admin", password_hash="x",
                     role="admin")
        s.add_all([cliente, ajeno, admin])
        s.commit()
        return {"sol": sol, "luna": luna, "torre": torre, "anexo": anexo,
                "patio": patio, "cliente": cliente, "ajeno": ajeno, "admin": admin}


@pytest.fixture()
def client(engine, carpeta):
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


def _subir(client, site, contenido=PDF, nombre="plano.pdf", kind="PLAN"):
    return client.post(
        "/api/documents",
        data={"site_id": str(site.id), "kind": kind},
        files={"file": (nombre, contenido, "application/octet-stream")},
    )


def _codigo(respuesta):
    return respuesta.json()["error"]["code"]


def _archivos(carpeta):
    return [p for p in carpeta.rglob("*") if p.is_file()]


# ---------------------------------------------------------
# SUBIDA
# ---------------------------------------------------------
@pytest.mark.parametrize(
    ("contenido", "nombre", "tipo"),
    [
        (PDF, "plano.pdf", "application/pdf"),
        (PNG, "foto.png", "image/png"),
        (JPG, "foto.jpg", "image/jpeg"),
        (CSV, "lecturas.csv", "text/csv"),
        (b"\xef\xbb\xbfa,b\n1,2\n", "bom.csv", "text/csv"),
        ("a;b\nCaña;1\n".encode("cp1252"), "excel.csv", "text/csv"),
    ],
)
def test_sube_los_tipos_admitidos(client, datos, carpeta, contenido, nombre, tipo):
    _entrar(client, datos["cliente"])
    respuesta = _subir(client, datos["torre"], contenido, nombre)

    assert respuesta.status_code == 201, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["content_type"] == tipo
    assert cuerpo["size"] == len(contenido)
    assert cuerpo["filename"] == nombre
    assert cuerpo["organization_id"] == str(datos["sol"].id)
    assert cuerpo["site_name"] == "Torre"
    assert cuerpo["uploaded_by"] == str(datos["cliente"].id)
    assert cuerpo["can_delete"] is True
    [archivo] = _archivos(carpeta)
    assert archivo.read_bytes() == contenido


def test_el_tipo_sale_del_contenido_no_de_la_extension(client, datos):
    _entrar(client, datos["cliente"])
    cuerpo = _subir(client, datos["torre"], PNG, "en-realidad.pdf").json()
    assert cuerpo["content_type"] == "image/png"


@pytest.mark.parametrize(
    "contenido", [EXE, b"GIF89a\x01\x00\x01\x00\x00\x00", b"texto\x00con nulo"]
)
def test_rechaza_lo_que_no_es_pdf_jpg_png_ni_csv(client, datos, carpeta, contenido):
    _entrar(client, datos["cliente"])
    respuesta = _subir(client, datos["torre"], contenido, "virus.pdf")

    assert respuesta.status_code == 422
    assert _codigo(respuesta) == "UNSUPPORTED_FILE_TYPE"
    assert _archivos(carpeta) == []


def test_rechaza_un_archivo_vacio(client, datos):
    _entrar(client, datos["cliente"])
    respuesta = _subir(client, datos["torre"], b"", "vacio.pdf")
    assert (respuesta.status_code, _codigo(respuesta)) == (422, "EMPTY_FILE")


def test_rechaza_un_archivo_demasiado_grande(client, datos, carpeta, monkeypatch):
    monkeypatch.setattr(app_settings, "MAX_UPLOAD_MB", 1)
    _entrar(client, datos["cliente"])

    justo = _subir(client, datos["torre"], PDF.ljust(1024 * 1024, b" "))
    grande = _subir(client, datos["torre"], PDF.ljust(1024 * 1024 + 1, b" "))

    assert justo.status_code == 201
    assert (grande.status_code, _codigo(grande)) == (413, "FILE_TOO_LARGE")
    assert len(_archivos(carpeta)) == 1


def test_rechaza_un_kind_desconocido(client, datos):
    _entrar(client, datos["cliente"])
    assert _subir(client, datos["torre"], kind="CONTRATO").status_code == 422


def test_un_cliente_no_sube_a_un_edificio_ajeno(client, datos, carpeta):
    _entrar(client, datos["cliente"])
    respuesta = _subir(client, datos["patio"])

    assert (respuesta.status_code, _codigo(respuesta)) == (404, "SITE_NOT_FOUND")
    assert _archivos(carpeta) == []


def test_el_admin_sube_a_cualquier_edificio(client, datos):
    _entrar(client, datos["admin"])
    cuerpo = _subir(client, datos["patio"]).json()
    assert cuerpo["organization_id"] == str(datos["luna"].id)


def test_sin_sesion_no_se_sube(client, datos):
    assert _subir(client, datos["torre"]).status_code == 401


@pytest.mark.parametrize(
    ("enviado", "guardado"),
    [
        ("C:\\Users\\ana\\plano.pdf", "plano.pdf"),
        ("../../etc/passwd", "passwd"),
        ("ma\x00l\x1f.pdf", "mal.pdf"),
        ("", "documento"),
        ("..", "documento"),
        ("a" * 300 + ".pdf", "a" * 251 + ".pdf"),
    ],
)
def test_limpia_el_nombre_del_archivo(enviado, guardado):
    assert clean_filename(enviado) == guardado


def test_el_archivo_no_se_guarda_con_el_nombre_del_usuario(client, datos, carpeta):
    _entrar(client, datos["cliente"])
    _subir(client, datos["torre"], nombre="../../fuera.pdf")

    [archivo] = _archivos(carpeta)
    assert archivo.parent == carpeta
    assert "fuera" not in archivo.name


# ---------------------------------------------------------
# LISTADO
# ---------------------------------------------------------
@pytest.fixture()
def tres(client, datos):
    """Torre: un PLAN del cliente y un REPORT del admin. Patio: un PLAN."""
    _entrar(client, datos["cliente"])
    plan = _subir(client, datos["torre"]).json()
    _entrar(client, datos["admin"])
    informe = _subir(client, datos["torre"], kind="REPORT").json()
    ajeno = _subir(client, datos["patio"]).json()
    client.cookies.clear()
    return {"plan": plan, "informe": informe, "ajeno": ajeno}


def _ids(respuesta):
    return {d["id"] for d in respuesta.json()["items"]}


def test_el_cliente_solo_ve_los_de_su_organizacion(client, datos, tres):
    _entrar(client, datos["cliente"])
    respuesta = client.get("/api/documents")

    assert _ids(respuesta) == {tres["plan"]["id"], tres["informe"]["id"]}
    assert respuesta.json()["total"] == 2


def test_un_cliente_que_pide_otra_organizacion_recibe_lista_vacia(client, datos, tres):
    _entrar(client, datos["cliente"])
    respuesta = client.get("/api/documents", params={"organization_id": str(datos["luna"].id)})
    assert respuesta.json()["items"] == []


def test_el_admin_ve_todos_y_filtra(client, datos, tres):
    _entrar(client, datos["admin"])

    assert len(_ids(client.get("/api/documents"))) == 3
    assert _ids(client.get("/api/documents", params={"site_id": str(datos["patio"].id)})) == {
        tres["ajeno"]["id"]
    }
    assert _ids(client.get("/api/documents", params={"kind": "REPORT"})) == {
        tres["informe"]["id"]
    }
    assert _ids(
        client.get("/api/documents", params={"organization_id": str(datos["sol"].id)})
    ) == {tres["plan"]["id"], tres["informe"]["id"]}


def test_can_delete_depende_de_quien_pregunta(client, datos, tres):
    _entrar(client, datos["cliente"])
    por_id = {d["id"]: d for d in client.get("/api/documents").json()["items"]}
    assert por_id[tres["plan"]["id"]]["can_delete"] is True
    assert por_id[tres["informe"]["id"]]["can_delete"] is False

    _entrar(client, datos["admin"])
    assert all(d["can_delete"] for d in client.get("/api/documents").json()["items"])


# ---------------------------------------------------------
# DESCARGA
# ---------------------------------------------------------
def test_descarga_el_archivo_con_su_nombre_y_tipo(client, datos, tres):
    _entrar(client, datos["cliente"])
    respuesta = client.get(f"/api/documents/{tres['plan']['id']}/download")

    assert respuesta.status_code == 200
    assert respuesta.content == PDF
    assert respuesta.headers["content-type"] == "application/pdf"
    assert respuesta.headers["content-disposition"].startswith("attachment")
    assert "plano.pdf" in respuesta.headers["content-disposition"]
    assert respuesta.headers["x-content-type-options"] == "nosniff"


def test_un_cliente_no_descarga_lo_de_otra_organizacion(client, datos, tres):
    _entrar(client, datos["cliente"])
    respuesta = client.get(f"/api/documents/{tres['ajeno']['id']}/download")
    assert (respuesta.status_code, _codigo(respuesta)) == (404, "DOCUMENT_NOT_FOUND")


def test_sin_sesion_no_se_descarga(client, tres):
    assert client.get(f"/api/documents/{tres['plan']['id']}/download").status_code == 401


def test_un_archivo_que_falta_en_el_disco_da_404(client, datos, tres, carpeta):
    for archivo in _archivos(carpeta):
        archivo.unlink()
    _entrar(client, datos["cliente"])
    respuesta = client.get(f"/api/documents/{tres['plan']['id']}/download")
    assert (respuesta.status_code, _codigo(respuesta)) == (404, "DOCUMENT_FILE_MISSING")


# ---------------------------------------------------------
# BORRADO
# ---------------------------------------------------------
def test_el_cliente_borra_lo_suyo_y_su_archivo(client, datos, tres, carpeta, engine):
    _entrar(client, datos["cliente"])
    respuesta = client.delete(f"/api/documents/{tres['plan']['id']}")

    assert respuesta.status_code == 204
    assert len(_archivos(carpeta)) == 2
    with Session(engine) as s:
        assert s.get(Document, UUID(tres["plan"]["id"])) is None


def test_el_cliente_no_borra_lo_que_subio_el_admin(client, datos, tres, carpeta):
    _entrar(client, datos["cliente"])
    respuesta = client.delete(f"/api/documents/{tres['informe']['id']}")

    assert (respuesta.status_code, _codigo(respuesta)) == (403, "DOCUMENT_UPLOADED_BY_ADMIN")
    assert len(_archivos(carpeta)) == 3


def test_el_cliente_no_borra_si_el_autor_ya_no_existe(client, datos, engine):
    _entrar(client, datos["cliente"])
    documento = _subir(client, datos["torre"]).json()
    with Session(engine) as s:
        s.execute(Document.__table__.update().values(uploaded_by=None))
        s.commit()

    respuesta = client.delete(f"/api/documents/{documento['id']}")
    assert respuesta.status_code == 403


def test_un_cliente_no_borra_lo_de_otra_organizacion(client, datos, tres):
    _entrar(client, datos["ajeno"])
    respuesta = client.delete(f"/api/documents/{tres['plan']['id']}")
    assert (respuesta.status_code, _codigo(respuesta)) == (404, "DOCUMENT_NOT_FOUND")


def test_el_admin_borra_cualquiera(client, datos, tres, carpeta):
    _entrar(client, datos["admin"])
    for documento in tres.values():
        assert client.delete(f"/api/documents/{documento['id']}").status_code == 204
    assert _archivos(carpeta) == []


def test_con_documentos_el_edificio_no_se_borra_y_sin_ellos_si(client, datos, tres):
    _entrar(client, datos["admin"])
    url = f"/api/sites/{datos['patio'].id}"

    assert _codigo(client.delete(url)) == "SITE_HAS_DOCUMENTS"
    client.delete(f"/api/documents/{tres['ajeno']['id']}")
    assert client.delete(url).status_code == 204


# ---------------------------------------------------------
# CONTRATO
# ---------------------------------------------------------
def test_el_openapi_publica_el_contrato(client):
    schemas = client.get("/api/openapi.json").json()["components"]["schemas"]
    assert schemas["DocumentKind"]["enum"] == ["PLAN", "REPORT", "INVOICE", "PHOTO", "OTHER"]
    assert "DocumentResponse" in schemas
