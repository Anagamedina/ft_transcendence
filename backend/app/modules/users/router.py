# ROUTER — users
# Thin HTTP layer: validates schemas → calls the service → answers.
"""
User endpoints. Two routers:

- `router`, My account: `/api/me` (issue #26 and B8). It is `/api/me` and
  not `/api/users/me` (section 9.1 of the document), so it has no
  `prefix`. It includes exporting my data and requesting deletion (B15,
  #149).
- `admin_router`, user management (B6, #141):

    GET    /api/users                 → list (organization_id, q, active)
    GET    /api/users/{id}            → detail
    PATCH  /api/users/{id}            → name, role and organization
    POST   /api/users/{id}/deactivate → can no longer log in
    POST   /api/users/{id}/activate   → can log in again
    DELETE /api/users/{id}            → remove access

  All admin only, with `require_role` on the whole router, as in
  organizations: a new route cannot forget it.

`UserResponse` is already published in the Swagger *Schemas* section.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status

from app.modules.auth.schemas import MessageResponse
from app.modules.users import emails
from app.modules.users.model import User
from app.modules.users.schemas import (
    CurrentSessionResponse,
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
    OptionalUser,
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

# Client writes: with the trial over, read-only (B12).
_SOLO_LECTURA_SI_CADUCA = [Depends(require_trial_not_expired)]
_PRUEBA_VENCIDA = error_response(
    status.HTTP_403_FORBIDDEN,
    "The trial is over and the account is read-only (`TRIAL_EXPIRED`).",
)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Who am I",
    description=(
        "Returns the user of the current session.\n\n"
        "With the session in an `httpOnly` cookie, the frontend cannot read "
        "who logged in: JavaScript has no access to that cookie. This call "
        "is its only way to know, and it is what it uses on start to decide "
        "which area to navigate to and which guards apply."
    ),
    responses={
        **error_response(
            status.HTTP_401_UNAUTHORIZED,
            "No session, or it has expired (`UNAUTHORIZED`).",
        ),
    },
)
def get_me(service: UserSvc, user: CurrentUser) -> MeResponse:
    return service.get_me(user)


@router.get(
    "/me/session",
    response_model=CurrentSessionResponse,
    summary="Is there a session?",
    description=(
        "The same as `GET /api/me`, but without a session it answers 200 "
        "with `user: null` instead of 401.\n\n"
        "It is what the frontend uses on start: opening the home page or "
        "the login without being logged in is normal, and a 401 would show "
        "up as an error in the browser console."
    ),
    responses={
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "Deactivated account or suspended organization (`ACCOUNT_DISABLED`).",
        ),
    },
)
def get_my_session(service: UserSvc, user: OptionalUser) -> CurrentSessionResponse:
    return CurrentSessionResponse(user=service.get_me(user) if user else None)


@router.patch(
    "/me",
    response_model=MeResponse,
    summary="Update my account",
    dependencies=_SOLO_LECTURA_SI_CADUCA,
    responses={
        **_PRUEBA_VENCIDA,
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "The name is not valid (`INVALID_NAME`).",
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
    summary="Change my password",
    dependencies=_SOLO_LECTURA_SI_CADUCA,
    responses={
        **_PRUEBA_VENCIDA,
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "The current password does not match (`WRONG_PASSWORD`) or the "
            "new one breaks the rules (`WEAK_PASSWORD`).",
        ),
    },
)
def change_password(
    payload: PasswordChange, service: UserSvc, user: CurrentUser
) -> MessageResponse:
    return service.change_password(user, payload)


# ---------------------------------------------------------
# USER MANAGEMENT (admin) — B6, issue #141
# ---------------------------------------------------------
admin_router = APIRouter(
    prefix="/users",
    tags=["Users"],
    dependencies=[Depends(require_role("admin"))],
)

Admin = Annotated[User, Depends(require_role("admin"))]

_SOLO_ADMIN = {
    **error_response(status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."),
    **error_response(
        status.HTTP_403_FORBIDDEN, "The session is not an admin one (`FORBIDDEN`)."
    ),
}
_NO_EXISTE = error_response(
    status.HTTP_404_NOT_FOUND, "The user does not exist (`USER_NOT_FOUND`)."
)


@admin_router.get(
    "",
    response_model=Page[UserAdminResponse],
    summary="List users",
    description=(
        "Users by name, with their organization, whether they are active "
        "and their last access.\n\n`q` searches the name and the email."
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
        Query(description="true: only active ones. false: only deactivated ones."),
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
    summary="Get a user",
    responses={**_SOLO_ADMIN, **_NO_EXISTE},
)
def get_user(user_id: UUID, service: UserSvc) -> UserAdminResponse:
    return service.get_user(user_id)


@admin_router.patch(
    "/{user_id}",
    response_model=UserAdminResponse,
    summary="Edit a user",
    description=(
        "Changes the name, the role or the organization: that is how a "
        "user is moved to another organization or given one. **The email "
        "is not editable**: sending it answers 422.\n\n"
        "An admin cannot remove their own admin role."
    ),
    responses={
        **_SOLO_ADMIN,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "The user (`USER_NOT_FOUND`) or the organization "
            "(`ORGANIZATION_NOT_FOUND`) does not exist.",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "An admin tries to remove their own role (`CANNOT_DEMOTE_SELF`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "A client would be left without an organization (`ORGANIZATION_REQUIRED`), "
            "empty name (`INVALID_NAME`) or a field that cannot be edited "
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
    summary="Deactivate a user",
    description=(
        "The user can no longer log in (403 `ACCOUNT_DISABLED`), also if "
        "they already had an open session. An admin cannot deactivate "
        "themselves."
    ),
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT,
            "An admin tries to deactivate themselves (`CANNOT_DEACTIVATE_SELF`).",
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
    summary="Activate a user",
    responses={**_SOLO_ADMIN, **_NO_EXISTE},
)
def activate_user(
    user_id: UUID, service: UserSvc, admin: Admin
) -> UserAdminResponse:
    return service.set_active(admin, user_id, active=True)


@admin_router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a user's access",
    description=(
        "Deletes the user. The alerts they acknowledged, the documents they "
        "uploaded and the invitations they sent stay, without an author."
    ),
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT,
            "An admin tries to delete themselves (`CANNOT_DELETE_SELF`).",
        ),
    },
)
def delete_user(user_id: UUID, service: UserSvc, admin: Admin) -> None:
    service.delete_user(admin, user_id)


_SIN_SESION = error_response(
    status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."
)


@router.get(
    "/me/export",
    response_model=MyDataExport,
    summary="Download my data",
    description=(
        "Everything AquaGuard stores about your account: the account (with "
        "the version of the terms you accepted), your organization and its "
        "buildings.\n\n"
        "It downloads as `aquaguard-mis-datos_AAAA-MM-DD.json`. An admin "
        "without an organization only gets their account.\n\n"
        "Each download sends the email \"Has descargado tus datos de "
        "AquaGuard\" to the account address (B19), in the background: the "
        "response does not wait for the email and, if sending fails, it is "
        "only logged."
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
    # attachment: the browser saves it instead of showing it.
    response.headers["Content-Disposition"] = f'attachment; filename="{nombre}"'
    # Personal data: it must not stay in any cache.
    response.headers["Cache-Control"] = "no-store"
    # Sent after the response. With plain data, not with `user`: by then
    # the database session is already closed.
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
    summary="Request deletion",
    description=(
        "Records that you want to leave. **Nothing is deleted:** an admin "
        "handles it. Asking again does not change the date of the first "
        "request.\n\n"
        "The first time it sends the email \"Hemos recibido tu petición de "
        "baja\" (B19), in the background; asking again does not send "
        "another one. `GET /api/me` returns `deletion_requested_at` to show "
        "it has already been requested."
    ),
    responses={**_SIN_SESION},
)
def request_deletion(
    service: UserSvc, user: CurrentUser, background: BackgroundTasks
) -> DeletionRequestResponse:
    # Checked before calling the service, which is idempotent and answers
    # the same both times: only the first request sends the email.
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
