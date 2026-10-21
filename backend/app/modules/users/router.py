# ROUTER — users
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de usuarios. Dos routers:

- `router`, Mi cuenta: `/api/me` (issue #26 y B8). Es `/api/me` y no
  `/api/users/me` (apartado 9.1 del documento), por eso no lleva `prefix`.
  Incluye exportar mis datos y pedir la baja (B15, #149).
- `admin_router`, gestión de usuarios (B6, #141):

    GET    /api/users                 → lista (organization_id, q, active)
    GET    /api/users/{id}            → ficha
    PATCH  /api/users/{id}            → nombre, rol y organización
    POST   /api/users/{id}/deactivate → deja de poder entrar
    POST   /api/users/{id}/activate   → vuelve a poder entrar
    DELETE /api/users/{id}            → quitar el acceso

  Todas solo de admin, con el `require_role` en el router entero, como en
  organizaciones: una ruta nueva no lo puede olvidar.

`UserResponse` ya está publicado en la sección *Schemas* de Swagger.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status

from app.modules.auth.schemas import MessageResponse
from app.modules.users import emails
from app.modules.users.model import User
from app.modules.users.schemas import (
    DeletionRequestResponse,
    MeResponse,
    MeUpdate,
    MyDataExport,
    PasswordChange,
    UserAdminResponse,
    UserUpdate,
)
from app.modules.users.service import UserService, get_user_service
from app.shared.dependencies import (
    CurrentUser,
    OrganizationIdFilter,
    Pagination,
    Search,
    require_role,
    require_trial_not_expired,
)
from app.shared.email import send_email
from app.shared.schemas import Page, error_response

router = APIRouter(tags=["Users"])

UserSvc = Annotated[UserService, Depends(get_user_service)]

# Escrituras de cliente: con la prueba vencida, solo lectura (B12).
_SOLO_LECTURA_SI_CADUCA = [Depends(require_trial_not_expired)]
_PRUEBA_VENCIDA = error_response(
    status.HTTP_403_FORBIDDEN,
    "La prueba ha vencido y la cuenta es de solo lectura (`TRIAL_EXPIRED`).",
)


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
    dependencies=_SOLO_LECTURA_SI_CADUCA,
    responses={
        **_PRUEBA_VENCIDA,
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
    dependencies=_SOLO_LECTURA_SI_CADUCA,
    responses={
        **_PRUEBA_VENCIDA,
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


# ---------------------------------------------------------
# GESTIÓN DE USUARIOS (admin) — B6, issue #141
# ---------------------------------------------------------
admin_router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(require_role("admin"))],
)

Admin = Annotated[User, Depends(require_role("admin"))]

_SOLO_ADMIN = {
    **error_response(status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."),
    **error_response(
        status.HTTP_403_FORBIDDEN, "La sesión no es de un admin (`FORBIDDEN`)."
    ),
}
_NO_EXISTE = error_response(
    status.HTTP_404_NOT_FOUND, "El usuario no existe (`USER_NOT_FOUND`)."
)


@admin_router.get(
    "",
    response_model=Page[UserAdminResponse],
    summary="Listar usuarios",
    description=(
        "Usuarios por nombre, con su organización, si están activos y su "
        "último acceso.\n\n`q` busca en el nombre y el email."
    ),
    responses={**_SOLO_ADMIN},
)
def list_users(
    service: UserSvc,
    pagination: Pagination,
    q: Search,
    organization_id: OrganizationIdFilter = None,
    active: Annotated[
        bool | None,
        Query(description="true: solo activos. false: solo desactivados."),
    ] = None,
) -> Page[UserAdminResponse]:
    return service.list_users(
        offset=pagination.offset,
        limit=pagination.limit,
        organization_id=organization_id,
        q=q,
        active=active,
    )


@admin_router.get(
    "/{user_id}",
    response_model=UserAdminResponse,
    summary="Ver un usuario",
    responses={**_SOLO_ADMIN, **_NO_EXISTE},
)
def get_user(user_id: UUID, service: UserSvc) -> UserAdminResponse:
    return service.get_user(user_id)


@admin_router.patch(
    "/{user_id}",
    response_model=UserAdminResponse,
    summary="Editar un usuario",
    description=(
        "Cambia el nombre, el rol o la organización: así se mueve un "
        "usuario a otra organización o se le da una. **El email no se "
        "edita**: enviarlo responde 422.\n\n"
        "Un admin no puede quitarse a sí mismo el rol de admin."
    ),
    responses={
        **_SOLO_ADMIN,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "El usuario (`USER_NOT_FOUND`) o la organización "
            "(`ORGANIZATION_NOT_FOUND`) no existen.",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "Un admin intenta quitarse su propio rol (`CANNOT_DEMOTE_SELF`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Un cliente quedaría sin organización (`ORGANIZATION_REQUIRED`), "
            "nombre vacío (`INVALID_NAME`) o un campo que no se puede editar "
            "(`VALIDATION_ERROR`).",
        ),
    },
)
def update_user(
    user_id: UUID, payload: UserUpdate, service: UserSvc, admin: Admin
) -> UserAdminResponse:
    return service.update_user(admin, user_id, payload)


@admin_router.post(
    "/{user_id}/deactivate",
    response_model=UserAdminResponse,
    summary="Desactivar un usuario",
    description=(
        "Deja de poder entrar (403 `ACCOUNT_DISABLED`), también si ya tenía "
        "la sesión abierta. Un admin no puede desactivarse a sí mismo."
    ),
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT,
            "Un admin intenta desactivarse a sí mismo (`CANNOT_DEACTIVATE_SELF`).",
        ),
    },
)
def deactivate_user(
    user_id: UUID, service: UserSvc, admin: Admin
) -> UserAdminResponse:
    return service.set_active(admin, user_id, active=False)


@admin_router.post(
    "/{user_id}/activate",
    response_model=UserAdminResponse,
    summary="Activar un usuario",
    responses={**_SOLO_ADMIN, **_NO_EXISTE},
)
def activate_user(
    user_id: UUID, service: UserSvc, admin: Admin
) -> UserAdminResponse:
    return service.set_active(admin, user_id, active=True)


@admin_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Quitar el acceso a un usuario",
    description=(
        "Borra el usuario. Las alertas que reconoció, los documentos que "
        "subió y las invitaciones que envió se quedan, sin autor."
    ),
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT,
            "Un admin intenta borrarse a sí mismo (`CANNOT_DELETE_SELF`).",
        ),
    },
)
def delete_user(user_id: UUID, service: UserSvc, admin: Admin) -> None:
    service.delete_user(admin, user_id)


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
        "organización recibe solo su cuenta.\n\n"
        "Cada descarga envía el email «Has descargado tus datos de AquaGuard» "
        "a la dirección de la cuenta (B19), en segundo plano: la respuesta no "
        "espera al correo y, si el envío falla, solo se anota en el log."
    ),
    responses={**_SIN_SESION},
)
def export_me(
    service: UserSvc,
    user: CurrentUser,
    response: Response,
    background: BackgroundTasks,
) -> MyDataExport:
    datos = service.export_me(user)
    nombre = f"aquaguard-mis-datos_{datos.exported_at:%Y-%m-%d}.json"
    # attachment: el navegador lo guarda en vez de enseñarlo.
    response.headers["Content-Disposition"] = f'attachment; filename="{nombre}"'
    # Datos personales: que no se queden en ninguna caché.
    response.headers["Cache-Control"] = "no-store"
    # Se envía después de la respuesta. Con datos simples, no con `user`:
    # para entonces la sesión de la base de datos ya está cerrada.
    background.add_task(
        send_email,
        user.email,
        emails.EXPORT_SUBJECT,
        emails.export_body(user.name, datos.exported_at),
    )
    return datos


@router.post(
    "/me/deletion-request",
    response_model=DeletionRequestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Pedir la baja",
    description=(
        "Registra que quieres darte de baja. **No borra nada:** lo tramita un "
        "admin. Pedirla otra vez no cambia la fecha de la primera.\n\n"
        "La primera vez envía el email «Hemos recibido tu petición de baja» "
        "(B19), en segundo plano; pedirla otra vez no envía otro. "
        "`GET /api/me` devuelve `deletion_requested_at` para mostrar que ya "
        "está pedida."
    ),
    responses={**_SIN_SESION},
)
def request_deletion(
    service: UserSvc, user: CurrentUser, background: BackgroundTasks
) -> DeletionRequestResponse:
    # Se mira antes de llamar al servicio, que es idempotente y responde
    # igual las dos veces: solo la primera petición manda el email.
    primera_vez = user.deletion_requested_at is None
    respuesta = service.request_deletion(user)
    if primera_vez:
        background.add_task(
            send_email,
            user.email,
            emails.DELETION_SUBJECT,
            emails.deletion_body(user.name, respuesta.deletion_requested_at),
        )
    return respuesta
