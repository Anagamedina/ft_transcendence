"""
Regla común de contraseñas (B10, issue #140).

Se define aquí, y no en el registro, porque la usan todas las rutas donde
alguien elige contraseña: el registro público (B10), aceptar una
invitación (B4) y cambiarla desde «Mi cuenta» (B8). Si cada una tuviera
su propia regla, acabarían siendo distintas.

La regla (B10, 12-10-2026):

- **12 caracteres como mínimo y 128 como máximo.** El máximo no es por
  seguridad: Argon2 tarda más cuanto más larga es la contraseña, y sin
  tope un texto de un mega dejaría el servidor ocupado.
- **No puede ser una contraseña común** (lista de abajo) ni repetir casi
  siempre el mismo carácter (`aaaaaaaaaaaa`, `121212121212`).
- **No puede contener el email** de la cuenta: es lo primero que se prueba.

Todo responde 422 `WEAK_PASSWORD`, con un mensaje que dice qué falla
para que el formulario lo pueda enseñar junto al campo.

La comprobación vive en el service y no en el schema a propósito: así el
error tiene su propio código en vez del `VALIDATION_ERROR` genérico, y el
login (que no debe validar nada de esto) no la hereda por accidente.
"""

from __future__ import annotations

from app.core.exceptions import DomainValidationError

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128

# Con 12 caracteres de mínimo, las de las listas típicas («123456»,
# «qwerty») ya fallan por largo. Aquí van las que pasan de 12 y aun así
# son de las primeras que prueba cualquiera. Se comparan en minúsculas.
_COMUNES = frozenset(
    {
        "123456789012",
        "1234567890123",
        "12345678901234",
        "123456789000",
        "000000000000",
        "111111111111",
        "123123123123",
        "qwertyuiopas",
        "qwertyuiop123",
        "qwerty123456",
        "asdfghjklñ12",
        "1q2w3e4r5t6y",
        "1qaz2wsx3edc",
        "zaq12wsxcde3",
        "password1234",
        "password12345",
        "passwordpassword",
        "mypassword123",
        "contraseña123",
        "contrasena123",
        "contraseña1234",
        "contrasena1234",
        "micontraseña1",
        "micontrasena1",
        "iloveyou1234",
        "teamo1234567",
        "abcdefghijkl",
        "abcdefg12345",
        "abc123456789",
        "welcome12345",
        "bienvenido123",
        "administrator",
        "administrador",
        "aquaguard123",
        "aquaguard1234",
        "aquaguard2026",
    }
)

# Menos caracteres distintos que esto es repetir lo mismo: `aaaaaaaaaaaa`,
# `121212121212`, `abcabcabcabc`.
_MINIMO_DISTINTOS = 5


def check_password(password: str, email: str | None = None) -> None:
    """
    Corta con 422 `WEAK_PASSWORD` si la contraseña no cumple la regla.

    `email` es el de la cuenta a la que va la contraseña; si se pasa, la
    contraseña no puede contenerlo (ni su parte antes de la `@`).
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        _debil(f"La contraseña tiene que tener al menos {PASSWORD_MIN_LENGTH} caracteres.")
    if len(password) > PASSWORD_MAX_LENGTH:
        _debil(f"La contraseña no puede pasar de {PASSWORD_MAX_LENGTH} caracteres.")

    minusculas = password.lower()
    if minusculas in _COMUNES or len(set(minusculas)) < _MINIMO_DISTINTOS:
        _debil("Esa contraseña es demasiado fácil de adivinar. Elige otra.")

    if email:
        email = email.strip().lower()
        usuario = email.split("@", 1)[0]
        # Un usuario de 1-3 letras («ana») aparece en muchas contraseñas
        # sin que tenga nada que ver con el email.
        if email in minusculas or (len(usuario) >= 4 and usuario in minusculas):
            _debil("La contraseña no puede contener tu email.")


def _debil(mensaje: str) -> None:
    raise DomainValidationError(mensaje, code="WEAK_PASSWORD")
