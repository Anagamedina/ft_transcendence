"""
Shared password rule (B10, issue #140).

It is defined here, and not in the sign-up, because every route where
someone chooses a password uses it: the public sign-up (B10), accepting
an invitation (B4) and changing it from "Mi cuenta" (B8). If each had its
own rule, they would end up different.

The rule (B10, 2026-10-12):

- **12 characters minimum and 128 maximum.** The maximum is not about
  security: Argon2 takes longer the longer the password, and without a
  cap a one-megabyte text would keep the server busy.
- **It cannot be a common password** (list below) nor repeat almost
  always the same character (`aaaaaaaaaaaa`, `121212121212`).
- **It cannot contain the account email**: it is the first thing anyone
  tries.

Everything answers 422 `WEAK_PASSWORD`, with a message that says what
fails so the form can show it next to the field.

The check lives in the service and not in the schema on purpose: the
error gets its own code instead of the generic `VALIDATION_ERROR`, and
login (which must not validate any of this) does not inherit it by
accident.
"""

from __future__ import annotations

from app.core.exceptions import DomainValidationError

PASSWORD_MIN_LENGTH = 12
PASSWORD_MAX_LENGTH = 128

# With a 12-character minimum, the usual list entries ("123456",
# "qwerty") already fail on length. These are the ones longer than 12
# that are still among the first anyone tries. Compared in lowercase.
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

# Fewer distinct characters than this is repeating the same thing:
# `aaaaaaaaaaaa`, `121212121212`, `abcabcabcabc`.
_MINIMO_DISTINTOS = 5


def check_password(password: str, email: str | None = None) -> None:
    """
    Stops with 422 `WEAK_PASSWORD` if the password breaks the rule.

    `email` is the one of the account the password is for; if given, the
    password cannot contain it (nor its part before the `@`).
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
        # A 1-3 letter user name ("ana") shows up in many passwords that
        # have nothing to do with the email.
        if email in minusculas or (len(usuario) >= 4 and usuario in minusculas):
            _debil("La contraseña no puede contener tu email.")


def _debil(mensaje: str) -> None:
    raise DomainValidationError(mensaje, code="WEAK_PASSWORD")
