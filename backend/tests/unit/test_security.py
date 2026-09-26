"""
Tests de `app/core/security.py` (issue #26).

No tocan base de datos ni levantan la aplicación: este módulo es solo
criptografía, y se prueba solo.
"""

import time
from uuid import uuid4

import pytest

from app.core import security
from app.core.app_config import app_settings


# ---------------------------------------------------------
# Hash de contraseñas
# ---------------------------------------------------------
def test_la_huella_no_contiene_la_contrasena():
    """Lo más básico: que no se guarde en claro."""
    huella = security.hash_password("una-contrasena-larga")

    assert "una-contrasena-larga" not in huella
    assert huella.startswith("$argon2")


def test_la_contrasena_correcta_verifica():
    huella = security.hash_password("una-contrasena-larga")

    assert security.verify_password("una-contrasena-larga", huella) is True


def test_la_contrasena_equivocada_no_verifica():
    huella = security.hash_password("una-contrasena-larga")

    assert security.verify_password("otra-contrasena", huella) is False
    assert security.verify_password("", huella) is False


def test_dos_personas_con_la_misma_contrasena_tienen_huellas_distintas():
    """
    Cada huella lleva su propia sal, un valor aleatorio que se mezcla antes
    de calcularla. Sin eso, ver dos huellas iguales delataría que dos
    cuentas comparten contraseña.
    """
    una = security.hash_password("la-misma")
    otra = security.hash_password("la-misma")

    assert una != otra
    assert security.verify_password("la-misma", una)
    assert security.verify_password("la-misma", otra)


def test_una_huella_corrupta_no_revienta():
    """
    Devuelve False en vez de lanzar. Si se escapara la excepción, el login
    contra una fila estropeada daría un 500 en lugar del 401 que toca.
    """
    assert security.verify_password("lo-que-sea", "esto-no-es-una-huella") is False
    assert security.verify_password("lo-que-sea", "") is False


def test_needs_rehash_es_falso_con_una_huella_recien_hecha():
    huella = security.hash_password("una-contrasena-larga")

    assert security.needs_rehash(huella) is False
    assert security.needs_rehash("esto-no-es-una-huella") is False


# ---------------------------------------------------------
# Cookie de sesión
# ---------------------------------------------------------
def test_el_id_sobrevive_al_viaje_de_ida_y_vuelta():
    user_id = uuid4()

    token = security.create_session_token(user_id)

    assert security.read_session_token(token) == user_id


def test_un_token_manipulado_no_vale():
    """
    Firmado, no cifrado: el id se puede leer, pero cambiarlo rompe la firma.
    """
    token = security.create_session_token(uuid4())
    manipulado = token[:-1] + ("A" if token[-1] != "A" else "B")

    assert security.read_session_token(manipulado) is None


def test_un_token_firmado_con_otra_clave_no_vale(monkeypatch):
    """
    Quien no tenga el SECRET_KEY no puede fabricarse una sesión.
    """
    monkeypatch.setattr(app_settings, "SECRET_KEY", "la-clave-de-un-atacante")
    ajeno = security.create_session_token(uuid4())

    monkeypatch.setattr(app_settings, "SECRET_KEY", "la-clave-buena")

    assert security.read_session_token(ajeno) is None


def test_un_token_caducado_no_vale(monkeypatch):
    """
    Ojo con el reloj: itsdangerous guarda la marca de tiempo con resolución
    de un segundo, y compara con `edad > max_age`. Poniendo `max_age=1` y
    esperando 1,1 s, la edad puede salir exactamente 1 y el test pasaría o
    fallaría según en qué momento del segundo arranque.

    Con `max_age=0` no hay duda: tras esperar más de un segundo la edad es
    al menos 1, y 1 > 0 siempre.
    """
    token = security.create_session_token(uuid4())

    monkeypatch.setattr(security, "SESSION_MAX_AGE_SECONDS", 0)
    time.sleep(1.1)

    assert security.read_session_token(token) is None


def test_basura_en_la_cookie_no_revienta():
    assert security.read_session_token("") is None
    assert security.read_session_token("no-es-un-token") is None


def test_la_cookie_no_lleva_mas_que_el_id(monkeypatch):
    """
    Dentro va solo el id del usuario, ni el rol ni la organización: así,
    cambiarle el rol a alguien tiene efecto en la siguiente petición y no
    cuando vuelva a entrar.
    """
    from itsdangerous import URLSafeTimedSerializer

    user_id = uuid4()
    token = security.create_session_token(user_id)

    contenido = URLSafeTimedSerializer(
        app_settings.SECRET_KEY, salt="aquaguard.session.v1"
    ).loads(token)

    assert contenido == str(user_id)
