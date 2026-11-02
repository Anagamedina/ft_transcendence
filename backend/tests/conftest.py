import pytest

from app.core.app_config import app_settings


# TestClient habla por http://testserver, y por http no se reenvía una cookie
# marcada como Secure. El .env trae COOKIE_SECURE=true (el gateway sirve HTTPS),
# así que los tests la desactivan para no depender del .env de cada uno.
@pytest.fixture(autouse=True)
def cookie_without_secure(monkeypatch):
    monkeypatch.setattr(app_settings, "COOKIE_SECURE", False)


# Dentro de Docker, Compose pone SMTP_HOST=mailpit (B19). Ningún test debe
# mandar correo de verdad ni depender de que Mailpit esté arrancado: con
# SMTP_HOST vacío, `send_email` solo lo anota en el log. Los tests de B19
# cambian `send_email` por uno falso o vuelven a poner un host a propósito.
@pytest.fixture(autouse=True)
def smtp_disabled(monkeypatch):
    monkeypatch.setattr(app_settings, "SMTP_HOST", "")
