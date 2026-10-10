import pytest

from app.core.app_config import app_settings


# TestClient habla por http://testserver, y por http no se reenvía una cookie
# marcada como Secure. El .env trae COOKIE_SECURE=true (el gateway sirve HTTPS),
# así que los tests la desactivan para no depender del .env de cada uno.
@pytest.fixture(autouse=True)
def cookie_without_secure(monkeypatch):
    monkeypatch.setattr(app_settings, "COOKIE_SECURE", False)
