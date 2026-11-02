"""
Emails de confirmación del módulo GDPR (B19, issue #242).

Criterios de la issue:

- descargar los datos y pedir la baja envían un email cada uno;
- pedir la baja otra vez no envía un segundo email;
- con el servidor SMTP caído, las dos operaciones siguen respondiendo bien.

Los tests de los endpoints cambian `send_email` por uno falso que guarda
las llamadas. Los de `send_email` cambian `smtplib.SMTP` por uno falso:
ninguno abre una conexión de verdad.
"""

import logging
import smtplib
from datetime import datetime, timezone

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
from app.modules.users import emails
from app.modules.users import router as users_router
from app.modules.users.model import User
from app.shared import email as email_module


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
def usuario(engine):
    with Session(engine, expire_on_commit=False) as s:
        mar = Organization(name="Hotel Mar")
        s.add(mar)
        s.flush()
        cliente = User(
            organization_id=mar.id,
            email="ana@hotelmar.dev",
            name="Ana Medina",
            password_hash=hash_password("una-contraseña-larga"),
            role="client",
        )
        s.add(cliente)
        s.commit()
        return cliente


@pytest.fixture()
def cliente(engine, usuario):
    def _get_db():
        db = Session(engine, expire_on_commit=False)
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    client = TestClient(app)
    client.cookies.set(SESSION_COOKIE, create_session_token(usuario.id))
    yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def enviados(monkeypatch):
    """`send_email` falso: guarda (to, subject, body) en vez de enviar."""
    llamadas = []
    monkeypatch.setattr(
        users_router,
        "send_email",
        lambda to, subject, body: llamadas.append((to, subject, body)),
    )
    return llamadas


# ---------------------------------------------------------
# GET /api/me/export
# ---------------------------------------------------------
def test_descargar_los_datos_envia_un_email(cliente, enviados):
    respuesta = cliente.get("/api/me/export")

    assert respuesta.status_code == 200
    assert len(enviados) == 1
    to, subject, body = enviados[0]
    assert to == "ana@hotelmar.dev"
    assert subject == "Has descargado tus datos de AquaGuard"
    assert "Ana Medina" in body


def test_cada_descarga_envia_su_email(cliente, enviados):
    cliente.get("/api/me/export")
    cliente.get("/api/me/export")

    assert len(enviados) == 2


def test_sin_sesion_no_se_envia_nada(cliente, enviados):
    cliente.cookies.clear()

    respuesta = cliente.get("/api/me/export")

    assert respuesta.status_code == 401
    assert enviados == []


# ---------------------------------------------------------
# POST /api/me/deletion-request
# ---------------------------------------------------------
def test_pedir_la_baja_envia_un_email(cliente, enviados):
    respuesta = cliente.post("/api/me/deletion-request")

    assert respuesta.status_code == 202
    assert len(enviados) == 1
    to, subject, body = enviados[0]
    assert to == "ana@hotelmar.dev"
    assert subject == "Hemos recibido tu petición de baja"
    assert "Todavía no se ha borrado nada" in body


def test_pedir_la_baja_otra_vez_no_envia_otro_email(cliente, enviados):
    cliente.post("/api/me/deletion-request")
    segunda = cliente.post("/api/me/deletion-request")

    assert segunda.status_code == 202
    assert len(enviados) == 1


# ---------------------------------------------------------
# CON EL SERVIDOR SMTP CAÍDO
# ---------------------------------------------------------
class _SmtpCaido:
    """Como `smtplib.SMTP` con Mailpit parado: la conexión se rechaza."""

    def __init__(self, *args, **kwargs):
        raise ConnectionRefusedError(111, "Connection refused")


def test_con_el_smtp_caido_las_operaciones_responden_bien(
    cliente, monkeypatch, caplog
):
    monkeypatch.setattr(app_settings, "SMTP_HOST", "mailpit")
    monkeypatch.setattr(smtplib, "SMTP", _SmtpCaido)

    with caplog.at_level(logging.WARNING, logger="app.shared.email"):
        exportar = cliente.get("/api/me/export")
        baja = cliente.post("/api/me/deletion-request")

    assert exportar.status_code == 200
    assert baja.status_code == 202
    # El fallo queda en el log, uno por email
    assert len([r for r in caplog.records if "No se ha podido enviar" in r.message]) == 2


# ---------------------------------------------------------
# send_email
# ---------------------------------------------------------
class _SmtpFalso:
    """Como `smtplib.SMTP`, pero guarda lo que habría enviado."""

    instancias = []

    def __init__(self, host, port, timeout):
        self.host, self.port, self.timeout = host, port, timeout
        self.tls = False
        self.login_con = None
        self.mensajes = []
        _SmtpFalso.instancias.append(self)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def starttls(self):
        self.tls = True

    def login(self, user, password):
        self.login_con = (user, password)

    def send_message(self, message):
        self.mensajes.append(message)


@pytest.fixture()
def smtp_falso(monkeypatch):
    _SmtpFalso.instancias = []
    monkeypatch.setattr(smtplib, "SMTP", _SmtpFalso)
    monkeypatch.setattr(app_settings, "SMTP_HOST", "mailpit")
    monkeypatch.setattr(app_settings, "SMTP_PORT", 1025)
    monkeypatch.setattr(app_settings, "SMTP_FROM", "no-reply@aquaguard.dev")
    monkeypatch.setattr(app_settings, "SMTP_USER", "")
    monkeypatch.setattr(app_settings, "SMTP_STARTTLS", False)
    return _SmtpFalso.instancias


def test_send_email_envia_texto_plano(smtp_falso):
    email_module.send_email("ana@hotelmar.dev", "Asunto", "Cuerpo del email")

    (smtp,) = smtp_falso
    assert (smtp.host, smtp.port) == ("mailpit", 1025)
    assert smtp.timeout > 0
    (mensaje,) = smtp.mensajes
    assert mensaje["To"] == "ana@hotelmar.dev"
    assert mensaje["From"] == "AquaGuard <no-reply@aquaguard.dev>"
    assert mensaje["Subject"] == "Asunto"
    assert mensaje.get_content_type() == "text/plain"
    assert mensaje.get_content().strip() == "Cuerpo del email"
    # Mailpit: sin STARTTLS y sin login
    assert smtp.tls is False
    assert smtp.login_con is None


def test_send_email_con_starttls_y_usuario(smtp_falso, monkeypatch):
    monkeypatch.setattr(app_settings, "SMTP_STARTTLS", True)
    monkeypatch.setattr(app_settings, "SMTP_USER", "aquaguard")
    monkeypatch.setattr(app_settings, "SMTP_PASSWORD", "secreto")

    email_module.send_email("ana@hotelmar.dev", "Asunto", "Cuerpo")

    (smtp,) = smtp_falso
    assert smtp.tls is True
    assert smtp.login_con == ("aquaguard", "secreto")


def test_send_email_sin_smtp_host_no_conecta(smtp_falso, monkeypatch, caplog):
    monkeypatch.setattr(app_settings, "SMTP_HOST", "")

    with caplog.at_level(logging.INFO, logger="app.shared.email"):
        email_module.send_email("ana@hotelmar.dev", "Asunto", "Cuerpo")

    assert smtp_falso == []
    assert "SMTP_HOST vacío" in caplog.text


def test_send_email_no_lanza_si_el_servidor_falla(monkeypatch, caplog):
    monkeypatch.setattr(app_settings, "SMTP_HOST", "mailpit")
    monkeypatch.setattr(smtplib, "SMTP", _SmtpCaido)

    with caplog.at_level(logging.WARNING, logger="app.shared.email"):
        email_module.send_email("ana@hotelmar.dev", "Asunto", "Cuerpo")

    assert "No se ha podido enviar" in caplog.text


# ---------------------------------------------------------
# Textos
# ---------------------------------------------------------
def test_los_textos_llevan_la_fecha_legible():
    momento = datetime(2026, 10, 21, 9, 5, tzinfo=timezone.utc)

    assert "21/10/2026 a las 09:05 (UTC)" in emails.export_body("Ana", momento)
    assert "21/10/2026 a las 09:05 (UTC)" in emails.deletion_body("Ana", momento)
