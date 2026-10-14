# ROUTER — users
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de usuarios.

`GET /api/me` (issue #26), Mi cuenta (B8, #144) y exportar mis datos y
pedir la baja (B15, #149).

Nótese que es `/api/me` y no `/api/users/me` (apartado 9.1 del
documento). Por eso este router no lleva `prefix`: el prefijo `/users`
aparecerá con la gestión de usuarios de la B6 (#141).

`UserResponse` ya está publicado en la sección *Schemas* de Swagger.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status

from app.modules.auth.schemas import MessageResponse
from app.modules.users.service import UserService, get_user_service
from app.modules.users.schemas import (
    DeletionRequestResponse,
    MeResponse,
    MeUpdate,
    MyDataExport,
    PasswordChange,
)
from app.shared.dependencies import CurrentUser
from app.shared.schemas import error_response

router = APIRouter(tags=["Users"])

UserSvc = Annotated[UserService, Depends(get_user_service)]


@router.get(
    "/me",
    response_model=MeResponse,
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
def get_me(service: UserSvc, user: CurrentUser) -> MeResponse:
    return service.get_me(user)


@router.patch(
    "/me",
    response_model=MeResponse,
    summary="Actualizar mi cuenta",
    responses={
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "El nombre no es válido (`INVALID_NAME`).",
        ),
    },
)
def update_me(
    payload: MeUpdate, service: UserSvc, user: CurrentUser
) -> MeResponse:
    return service.update_me(user, payload)


@router.post(
    "/me/password",
    response_model=MessageResponse,
    summary="Cambiar mi contraseña",
    responses={
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "La contraseña actual no coincide (`WRONG_PASSWORD`) o la nueva "
            "no cumple las reglas (`WEAK_PASSWORD`).",
        ),
    },
)
def change_password(
    payload: PasswordChange, service: UserSvc, user: CurrentUser
) -> MessageResponse:
    return service.change_password(user, payload)


_SIN_SESION = error_response(
    status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."
)


@router.get(
    "/me/export",
    response_model=MyDataExport,
    summary="Descargar mis datos",
    description=(
        "Todo lo que AquaGuard guarda de tu cuenta: la cuenta (con la versión "
        "de los términos que aceptaste), tu organización y sus edificios.\n\n"
        "Se descarga como `aquaguard-mis-datos_AAAA-MM-DD.json`. Un admin sin "
        "organización recibe solo su cuenta."
    ),
    responses={**_SIN_SESION},
)
def export_me(service: UserSvc, user: CurrentUser, response: Response) -> MyDataExport:
    datos = service.export_me(user)
    nombre = f"aquaguard-mis-datos_{datos.exported_at:%Y-%m-%d}.json"
    # attachment: el navegador lo guarda en vez de enseñarlo.
    response.headers["Content-Disposition"] = f'attachment; filename="{nombre}"'
    # Datos personales: que no se queden en ninguna caché.
    response.headers["Cache-Control"] = "no-store"
    return datos


@router.post(
    "/me/deletion-request",
    response_model=DeletionRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Pedir la baja",
    description=(
        "Registra que quieres darte de baja. **No borra nada:** lo tramita un "
        "admin. Pedirla otra vez no cambia la fecha de la primera.\n\n"
        "No se envía email de confirmación: el proyecto no envía emails. "
        "`GET /api/me` devuelve `deletion_requested_at` para mostrar que ya "
        "está pedida."
    ),
    responses={**_SIN_SESION},
)
def request_deletion(service: UserSvc, user: CurrentUser) -> DeletionRequestResponse:
    return service.request_deletion(user)
