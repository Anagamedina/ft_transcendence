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

from app.modules.users.schemas import UserCreate, UserResponse
from app.shared.schemas import ApiModel, ApiRequest


class RegisterRequest(UserCreate):
    """
    Alta de cuenta. Mismos campos que `UserCreate`.

    Se declara como subclase con nombre propio, en lugar de usar
    `UserCreate` directamente en la ruta, porque el nombre del schema es lo
    que aparece en OpenAPI: el frontend lee `RegisterRequest` y sabe a qué
    endpoint corresponde. Además permite que el registro evolucione
    (aceptar un código de invitación, por ejemplo) sin arrastrar el alta
    administrativa de usuarios.
    """


class LoginRequest(ApiRequest):
    email: EmailStr = Field(
        description="Email de la cuenta.", examples=["ana@aquaguard.dev"]
    )
    password: str = Field(
        min_length=1,
        description=(
            "Contraseña. Aquí NO se aplica el mínimo de 8 caracteres: al "
            "entrar hay que aceptar lo que el usuario teclee y responder "
            "401 si no coincide. Rechazarlo con un 422 por longitud "
            "revelaría qué contraseñas no existen en el sistema."
        ),
        examples=["una-contrasena-larga"],
    )


class SessionResponse(ApiModel):
    """
    Respuesta de `POST /api/auth/login` y `GET /api/auth/me`.

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
