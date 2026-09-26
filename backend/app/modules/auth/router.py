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

from app.core.security import SESSION_COOKIE, session_cookie_kwargs
from app.modules.auth.schemas import MessageResponse
from app.modules.auth.service import AuthService, get_auth_service

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
