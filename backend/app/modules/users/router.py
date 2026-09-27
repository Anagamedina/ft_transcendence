# ROUTER — users
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de usuarios.

El único endpoint del nivel Básico es de la issue #26, ya implementado:

    GET /api/me

Nótese que es `/api/me` y no `/api/users/me` (apartado 9.1 del
documento). Por eso este router no llevará `prefix` cuando se implemente:
el prefijo `/users` solo aparecerá con el CRUD del nivel Intermedio.

`UserResponse` ya está publicado en la sección *Schemas* de Swagger.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.modules.auth.schemas import SessionResponse
from app.modules.users.service import UserService, get_user_service
from app.shared.dependencies import CurrentUser
from app.shared.schemas import error_response

router = APIRouter(tags=["Users"])

UserSvc = Annotated[UserService, Depends(get_user_service)]


@router.get(
    "/me",
    response_model=SessionResponse,
    summary="Quién soy",
    description=(
        "Devuelve el usuario de la sesión actual.\n\n"
        "Con la sesión en una cookie `httpOnly`, el frontend no puede leer "
        "quién ha entrado: JavaScript no tiene acceso a esa cookie. Esta "
        "llamada es su única forma de saberlo, y es lo que usa al arrancar "
        "para decidir a qué área navega y qué guards aplica."
    ),
    responses={
        **error_response(
            status.HTTP_401_UNAUTHORIZED,
            "No hay sesión, o ha caducado (`UNAUTHORIZED`).",
        ),
    },
)
def get_me(service: UserSvc, user: CurrentUser) -> SessionResponse:
    return SessionResponse(user=service.get_me(user))
