# SECURITY — hash de contraseñas y firma de la cookie de sesión.
"""
Las dos operaciones criptográficas de la issue #26.

--------------------------------------------------------------------
QUÉ HACE Y QUÉ NO
--------------------------------------------------------------------
Aquí NO se decide nada de negocio: no se comprueba si un usuario existe,
ni si tiene permiso. Eso es del service. Este módulo solo sabe convertir
una contraseña en huella, comparar una contraseña con una huella, y meter
y sacar un identificador de una cadena firmada.

Se separa por dos motivos concretos:

1. Es lo único del backend que hay que revisar si mañana se cambia de
   algoritmo. Repartido por los services, ese cambio sería una búsqueda
   por todo el proyecto.
2. Se prueba solo, sin base de datos y sin levantar la aplicación.

--------------------------------------------------------------------
POR QUÉ ARGON2 Y NO UN HASH NORMAL
--------------------------------------------------------------------
`sha256("mi-contraseña")` es rapidísimo, y eso es justo el problema: una
tarjeta gráfica prueba miles de millones por segundo. Argon2 está diseñado
para ser **lento a propósito** y para consumir memoria, de modo que probar
a lo bruto salga caro aunque se roben las huellas.

Además sala cada contraseña automáticamente. La *sal* es un valor aleatorio
que se mezcla antes de calcular la huella y se guarda dentro de ella: hace
que dos personas con la misma contraseña tengan huellas distintas, y que no
sirva una tabla precalculada.

--------------------------------------------------------------------
POR QUÉ UNA COOKIE FIRMADA Y NO UN JWT EN localStorage
--------------------------------------------------------------------
Lo fija la ADR 0001. El resumen: lo que vive en `localStorage` lo lee
cualquier JavaScript de la página, así que un script inyectado se lleva la
sesión. Una cookie `httpOnly` no la puede leer JavaScript — solo viaja
sola en cada petición.

**Firmada no es lo mismo que cifrada.** Quien tenga la cookie puede leer el
id que lleva dentro; lo que no puede es cambiarlo, porque la firma dejaría
de cuadrar. Por eso dentro va solo el id del usuario: ningún dato que
importe que se lea.
"""

from __future__ import annotations

from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from app.core.app_config import app_settings

# Nombre de la cookie. Constante para que el router y los tests no la
# escriban a mano cada uno por su lado.
SESSION_COOKIE = "aquaguard_session"

# Cuánto vale una sesión antes de obligar a entrar otra vez. Ocho horas es
# una jornada: quien entra por la mañana no tiene que repetir al volver de
# comer, y la sesión no queda viva indefinidamente en un ordenador
# compartido.
SESSION_MAX_AGE_SECONDS = 8 * 60 * 60

# "Para qué" de la firma. Dos cadenas firmadas con la misma clave pero
# distinto `salt` no son intercambiables, así que un token de sesión no
# podría colarse mañana donde se espere uno de recuperar contraseña.
_SESSION_SALT = "aquaguard.session.v1"

_hasher = PasswordHasher()


def _serializer() -> URLSafeTimedSerializer:
    """
    Firmador de la cookie.

    Se construye en cada llamada en vez de guardarlo en una variable de
    módulo, y es a propósito: así lee `SECRET_KEY` en el momento de usarlo.
    Cacheado, un test que cambie la clave seguiría firmando con la vieja y
    pasaría por motivos equivocados.
    """
    return URLSafeTimedSerializer(app_settings.SECRET_KEY, salt=_SESSION_SALT)


def session_cookie_kwargs() -> dict[str, object]:
    """
    Atributos con los que se pone y se borra la cookie de sesión.

    Están aquí, y no escritos a mano en cada endpoint, porque **borrar una
    cookie exige repetir los mismos atributos con los que se puso**. Si el
    logout usara un `path` distinto del login, el navegador trataría la
    cookie como otra distinta y no la borraría: el usuario creería haber
    salido y seguiría dentro.

    - `httponly`: JavaScript no la puede leer (ADR 0001).
    - `secure`: solo viaja por HTTPS. En local va a False porque se sirve
      por http; en producción se activa desde el `.env`.
    - `samesite="lax"`: no se envía en peticiones que vengan de otra web,
      salvo al navegar. Corta el grueso de los ataques CSRF sin romper
      llegar a la aplicación desde un enlace externo.
    """
    return {
        "httponly": True,
        "secure": app_settings.COOKIE_SECURE,
        "samesite": "lax",
        "path": "/",
    }


def hash_password(password: str) -> str:
    """
    Convierte una contraseña en la huella que se guarda en la base.

    La cadena que sale ya lleva dentro el algoritmo, sus parámetros y la
    sal, así que no hay que guardar nada más en otra columna.
    """
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Comprueba si una contraseña corresponde a una huella.

    Devuelve `False` en lugar de lanzar excepción, también cuando la huella
    está corrupta o tiene un formato que Argon2 no reconoce. Quien llama
    solo necesita saber si entra o no entra, y un `InvalidHashError`
    escapándose desde aquí acabaría en un 500 en vez de en el 401 que toca.
    """
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """
    Dice si conviene volver a calcular la huella con los parámetros de hoy.

    Argon2 recomienda subir el coste según mejora el hardware. Cuando eso
    pase, las huellas viejas siguen siendo válidas pero se quedan flojas, y
    este es el momento de renovarlas: en el login ya tenemos la contraseña
    en claro, que es la única ocasión en que se puede rehacer.
    """
    try:
        return _hasher.check_needs_rehash(password_hash)
    except InvalidHashError:
        return False


def create_session_token(user_id: UUID) -> str:
    """
    Crea el contenido firmado de la cookie de sesión.

    Solo lleva el id del usuario. Ni el rol ni la organización: si fueran
    dentro, cambiarle el rol a alguien no tendría efecto hasta que volviera
    a entrar. Yendo solo el id, cada petición lee el usuario de la base y
    ve su estado real.
    """
    return _serializer().dumps(str(user_id))


def read_session_token(token: str) -> UUID | None:
    """
    Saca el id del usuario de la cookie, o `None` si no vale.

    Devuelve `None` en los tres casos en que no se puede confiar en ella:
    firma que no cuadra (manipulada o de otra clave), sesión caducada, o
    contenido que no es un UUID. Quien llama los trata igual — no hay
    sesión — y no conviene distinguirlos hacia fuera: decirle a alguien
    «tu firma es inválida» frente a «ha caducado» le da información sobre
    qué está fallando en su intento.
    """
    try:
        raw = _serializer().loads(token, max_age=SESSION_MAX_AGE_SECONDS)
    except (BadSignature, SignatureExpired):
        return None

    try:
        return UUID(raw)
    except (ValueError, TypeError, AttributeError):
        return None
