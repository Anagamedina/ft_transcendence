# ROUTER — auth
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de autenticación (`/api/auth/...`).

El router se registra desde la issue #22. Los endpoints son de la
issue #26:

    POST /api/auth/register   → pendiente: la tabla `users` no admite
                                 todavía lo que pide el contrato
    POST /api/auth/login      → pendiente
    POST /api/auth/logout     → implementado

El contrato de esos endpoints ya está definido en `schemas.py` y se
publica en la sección *Schemas* de Swagger (ver `app/openapi.py`), para
que Lylia pueda construir el `MockAdapter` sin esperar a la #26.

Cuando llegue el momento de implementarlos, hay un reparto que conviene
respetar: **la cookie de sesión la pone el router, no el service**. Una
cookie es una cabecera HTTP, y el service por definición no habla HTTP.

    service → comprueba las credenciales y devuelve el usuario
    router  → traduce eso a un `Set-Cookie`

Ver `docs/decisions/0001-auth-cookie.md`: la sesión viaja en una cookie
httpOnly, no en un JWT dentro del JSON.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.core.exceptions import ForbiddenError
from app.core.security import (
    SESSION_COOKIE,
    SESSION_MAX_AGE_SECONDS,
    create_session_token,
    session_cookie_kwargs,
)
from app.modules.auth.schemas import (
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    SessionResponse,
)
from app.modules.auth.service import AuthService, get_auth_service
from app.shared.dependencies import CurrentUser
from app.shared.schemas import error_response

router = APIRouter(prefix="/auth", tags=["Auth"])

AuthSvc = Annotated[AuthService, Depends(get_auth_service)]


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Cerrar sesión",
    description=(
        "Borra la cookie de sesión del navegador.\n\n"
        "**No exige estar autenticado a propósito.** Salir tiene que "
        "funcionar siempre: con la sesión caducada, con una cookie "
        "estropeada o sin ninguna. Si pidiera sesión válida, quien más "
        "necesita salir —alguien con una sesión en mal estado— sería "
        "justo quien no podría."
    ),
)
def logout(response: Response, service: AuthSvc) -> MessageResponse:
    # Del lado del servidor no hay nada que invalidar: la sesión es una
    # cookie firmada sin estado. Se llama igual porque es el sitio donde
    # entraría la revocación el día que exista (ver el service).
    service.logout()

    # Los atributos tienen que ser los mismos con los que se puso, o el
    # navegador la trataría como otra cookie distinta y no la borraría.
    response.delete_cookie(SESSION_COOKIE, **session_cookie_kwargs())

    return MessageResponse(message="Sesión cerrada.")


@router.post(
    "/login",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesión",
    description=(
        "Comprueba las credenciales y deja la sesión abierta en una cookie "
        "`httpOnly`.\n\n"
        "Devuelve el usuario, **no un token**: el token va en la cookie, "
        "donde JavaScript no lo puede leer (ADR 0001).\n\n"
        "Un email que no existe y una contraseña incorrecta responden lo "
        "mismo, y tardan lo mismo: distinguirlos permitiría averiguar qué "
        "cuentas hay dadas de alta."
    ),
    responses={
        **error_response(
            status.HTTP_401_UNAUTHORIZED,
            "Email o contraseña incorrectos (`UNAUTHORIZED`).",
        ),
    },
)
def login(
    payload: LoginRequest,
    response: Response,
    service: AuthSvc,
) -> SessionResponse:
    usuario = service.login(payload)

    # La cookie la pone el router, no el service: una cookie es una
    # cabecera HTTP, y el service no habla HTTP.
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(usuario.id),
        max_age=SESSION_MAX_AGE_SECONDS,
        **session_cookie_kwargs(),
    )

    return SessionResponse(user=usuario)


@router.post(
    "/register",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta una cuenta",
    description=(
        "Crea una cuenta de cliente dentro de la organización de quien la "
        "da de alta.\n\n"
        "**Exige sesión de administrador.** El equipo acordó que no hay "
        "registro público: las cuentas de cliente las crea un admin. Por "
        "eso este endpoint no abre sesión para el usuario creado — quien "
        "sigue dentro es el admin que lo dio de alta."
    ),
    responses={
        **error_response(
            status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."
        ),
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "La sesión no es de un administrador (`FORBIDDEN`).",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "Ese email ya existe (`EMAIL_ALREADY_EXISTS`).",
        ),
    },
)
def register(
    payload: RegisterRequest,
    service: AuthSvc,
    user: CurrentUser,
) -> SessionResponse:
    # Comprobación de rol a mano. Lo propio sería `require_role("admin")`,
    # pero esa dependencia es de la issue #27 y todavía lanza 501. Cuando
    # exista, esta línea se sustituye por la dependencia y el cuerpo se
    # queda solo con la llamada al service.
    if user.role != "admin":
        raise ForbiddenError("Solo un administrador puede dar de alta cuentas.")

    creado = service.register(
        payload,
        organization_id=user.organization_id,
        role="client",
    )
    return SessionResponse(user=creado)
