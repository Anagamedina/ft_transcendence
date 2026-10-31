# SCHEMAS — auth
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de autenticación (issue #23).

Detalle que condiciona todos estos schemas: **la sesión viaja en una
cookie httpOnly, no en el cuerpo de la respuesta** (ADR 0001,
`docs/decisions/0001-auth-cookie.md`).

Por eso no existe un `TokenResponse` con un `access_token` dentro. El
login devuelve el usuario y adjunta la cookie mediante la cabecera
`Set-Cookie`. Una cookie httpOnly no es legible desde JavaScript, lo que
cierra la vía de robo de token por XSS que tendría un JWT guardado en
`localStorage`.

Consecuencia para el frontend: hay que llamar con `withCredentials: true`
en Axios. Sin eso el navegador no envía la cookie y todo responde 401.
"""

from __future__ import annotations

from pydantic import EmailStr, Field

from app.modules.users.schemas import UserResponse
from app.shared.passwords import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH
from app.shared.schemas import ApiModel, ApiRequest, Password, RawPassword


class RegisterRequest(ApiRequest):
    """
    Registro público (B10, issue #140): cualquiera crea su cuenta y, con
    ella, su organización en prueba.

    Ya no hereda del antiguo `UserCreate`, que se eliminó. Hasta la B10
    el registro era el alta de un cliente por un admin, con
    `organization_id`; ahora quien se
    registra no tiene organización todavía: la crea con
    `organization_name`. Los usuarios de una organización que ya existe
    llegarán por invitación (B4).

    La contraseña solo se limita aquí a 128 caracteres. La regla de
    verdad (12 como mínimo, no común, sin el email) la aplica el service
    con `check_password`, para responder `WEAK_PASSWORD` y no el
    `VALIDATION_ERROR` genérico.
    """

    name: str = Field(
        min_length=1,
        max_length=120,
        description="Nombre de quien se registra.",
        examples=["Ana Medina"],
    )
    email: EmailStr = Field(
        description="Email de la cuenta. Único en todo el sistema.",
        examples=["ana@hotelmar.com"],
    )
    password: Password = Field(
        max_length=PASSWORD_MAX_LENGTH,
        description=(
            f"Al menos {PASSWORD_MIN_LENGTH} caracteres, que no sea una "
            "contraseña común ni contenga el email. Si no cumple, 422 "
            "`WEAK_PASSWORD`."
        ),
        examples=["agua-que-no-se-escapa"],
    )
    organization_name: str = Field(
        max_length=120,
        description=(
            "Nombre de la organización que se crea, en prueba. Único sin "
            "distinguir mayúsculas."
        ),
        examples=["Hotel Mar"],
    )
    accept_terms: bool = Field(
        description=(
            "Tiene que ser `true`: quien se registra acepta los términos "
            "de uso. Si no, 422 `TERMS_NOT_ACCEPTED`."
        ),
        examples=[True],
    )


class LoginRequest(ApiRequest):
    email: EmailStr = Field(
        description="Email de la cuenta.", examples=["ana@aquaguard.dev"]
    )
    password: RawPassword = Field(
        min_length=1,
        description=(
            "Contraseña. Aquí NO se aplica la regla de contraseñas: al "
            "entrar hay que aceptar lo que el usuario teclee y responder "
            "401 si no coincide. Rechazarlo con un 422 por longitud "
            "revelaría qué contraseñas no existen en el sistema. Se "
            "compara tal cual, sin recortar espacios, y una de más de "
            f"{PASSWORD_MAX_LENGTH} caracteres es 401 sin llegar a Argon2."
        ),
        examples=["una-contrasena-larga"],
    )


class SessionResponse(ApiModel):
    """
    Respuesta del login, del registro (B10) y de `GET /api/me`.

    Devuelve el usuario, no un token: el token va en la cookie.
    """

    user: UserResponse


class MessageResponse(ApiModel):
    """
    Respuesta de operaciones sin contenido propio, como el logout.

    Se prefiere a un `204 No Content` porque el frontend ya tiene un
    manejador común que espera cuerpo JSON en toda la API, y un 204 sin
    cuerpo obligaría a un caso especial.
    """

    message: str = Field(examples=["Sesión cerrada."])
