# ROUTER — invitations
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Invitaciones (B4, issue #141). Contrato en `schemas.py`.

    POST   /api/invitations                        admin   → código y enlace (201)
    GET    /api/invitations                        admin   → lista
    DELETE /api/invitations/{id}                   admin   → revocar (204)
    POST   /api/invitations/{id}/resend            admin   → código nuevo
    GET    /api/invitations/by-code/{code}         público → lo justo para el formulario
    POST   /api/invitations/by-code/{code}/accept  público → crea el usuario y abre sesión (201)

Las rutas de admin llevan el `require_role` una a una, no en el router,
porque las dos públicas cuelgan del mismo prefijo. Esas dos son las que
el gateway limita por IP (`location /api/invitations/by-code/`).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Path, Query, Response, status

from app.core.security import (
    SESSION_COOKIE,
    SESSION_MAX_AGE_SECONDS,
    create_session_token,
    session_cookie_kwargs,
)
from app.modules.auth.schemas import SessionResponse
from app.modules.invitations.schemas import (
    InvitationAccept,
    InvitationCreate,
    InvitationPublicResponse,
    InvitationResponse,
    InvitationSentResponse,
)
from app.modules.invitations.service import (
    InvitationService,
    get_invitation_service,
)
from app.modules.users.model import User
from app.shared.dependencies import OrganizationIdFilter, Pagination, require_role
from app.shared.enums import InvitationStatus
from app.shared.schemas import Page, error_response

router = APIRouter(prefix="/invitations", tags=["Invitations"])

InvitationSvc = Annotated[InvitationService, Depends(get_invitation_service)]
Admin = Annotated[User, Depends(require_role("admin"))]
# Un código de `token_urlsafe` tiene 24 caracteres; el tope solo evita que
# llegue cualquier cosa hasta la base.
Code = Annotated[str, Path(min_length=1, max_length=64)]

_SOLO_ADMIN = {
    **error_response(status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."),
    **error_response(
        status.HTTP_403_FORBIDDEN, "La sesión no es de un admin (`FORBIDDEN`)."
    ),
}
_NO_EXISTE = error_response(
    status.HTTP_404_NOT_FOUND, "La invitación no existe (`INVITATION_NOT_FOUND`)."
)
_ENLACE = {
    **error_response(
        status.HTTP_404_NOT_FOUND,
        "El código no existe, ya se usó o se revocó (`INVITATION_NOT_FOUND`).",
    ),
    **error_response(
        status.HTTP_410_GONE, "La invitación ha caducado (`INVITATION_EXPIRED`)."
    ),
}


# ---------------------------------------------------------
# ADMIN
# ---------------------------------------------------------
@router.post(
    "",
    response_model=InvitationSentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invitar a un email",
    description=(
        "Crea una invitación a la organización, válida "
        "`INVITATION_TTL_DAYS` días (7 por defecto).\n\n"
        "**`code` y `url` solo salen en esta respuesta**: en la base se "
        "guarda su hash. El enlace no se envía por correo; el admin lo "
        "hace llegar."
    ),
    responses={
        **_SOLO_ADMIN,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "La organización no existe (`ORGANIZATION_NOT_FOUND`).",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "Ese email ya tiene cuenta (`EMAIL_ALREADY_EXISTS`) o una "
            "invitación vigente en esa organización (`INVITATION_ALREADY_PENDING`).",
        ),
    },
)
def create_invitation(
    payload: InvitationCreate, service: InvitationSvc, admin: Admin
) -> InvitationSentResponse:
    return service.create(admin, payload)


@router.get(
    "",
    response_model=Page[InvitationResponse],
    summary="Listar invitaciones",
    description=(
        "Las más recientes primero, sin el código. `status=PENDING` deja "
        "las que todavía se pueden aceptar."
    ),
    responses={**_SOLO_ADMIN},
)
def list_invitations(
    service: InvitationSvc,
    pagination: Pagination,
    _admin: Admin,
    organization_id: OrganizationIdFilter = None,
    status_filtro: Annotated[
        InvitationStatus | None,
        Query(alias="status", description="Deja solo las invitaciones en ese estado."),
    ] = None,
) -> Page[InvitationResponse]:
    return service.list(
        offset=pagination.offset,
        limit=pagination.limit,
        organization_id=organization_id,
        status=status_filtro,
    )


@router.delete(
    "/{invitation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revocar una invitación",
    description="El enlace deja de valer. Revocar dos veces no es un error.",
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT, "Ya se aceptó (`INVITATION_NOT_PENDING`)."
        ),
    },
)
def revoke_invitation(
    invitation_id: UUID, service: InvitationSvc, _admin: Admin
) -> Response:
    service.revoke(invitation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{invitation_id}/resend",
    response_model=InvitationSentResponse,
    summary="Reenviar una invitación",
    description=(
        "Código nuevo y otros `INVITATION_TTL_DAYS` días. El enlace "
        "anterior deja de valer. Sirve también para una caducada."
    ),
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT,
            "Ya se aceptó o se revocó (`INVITATION_NOT_PENDING`).",
        ),
    },
)
def resend_invitation(
    invitation_id: UUID, service: InvitationSvc, _admin: Admin
) -> InvitationSentResponse:
    return service.resend(invitation_id)


# ---------------------------------------------------------
# PÚBLICO
# ---------------------------------------------------------
@router.get(
    "/by-code/{code}",
    response_model=InvitationPublicResponse,
    summary="Abrir un enlace de invitación",
    description="Sin sesión. Lo justo para el formulario de aceptar.",
    responses={**_ENLACE},
)
def get_invitation_by_code(code: Code, service: InvitationSvc) -> InvitationPublicResponse:
    return service.get_by_code(code)


@router.post(
    "/by-code/{code}/accept",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Aceptar una invitación",
    description=(
        "Sin sesión. Crea la cuenta de cliente en la organización de la "
        "invitación, con su email, y **deja la sesión abierta**, como el "
        "registro. El enlace no vuelve a valer."
    ),
    responses={
        **_ENLACE,
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "La organización está suspendida (`ACCOUNT_DISABLED`).",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "Ese email ya tiene cuenta (`EMAIL_ALREADY_EXISTS`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Términos sin aceptar (`TERMS_NOT_ACCEPTED`), contraseña débil "
            "(`WEAK_PASSWORD`) o nombre vacío (`VALIDATION_ERROR`).",
        ),
    },
)
def accept_invitation(
    code: Code,
    payload: InvitationAccept,
    response: Response,
    service: InvitationSvc,
) -> SessionResponse:
    creado = service.accept(code, payload)

    # Como en el login y el registro: la cookie la pone el router.
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(creado.id),
        max_age=SESSION_MAX_AGE_SECONDS,
        **session_cookie_kwargs(),
    )
    return SessionResponse(user=creado)
