# ROUTER — invitations
# Thin HTTP layer: validates schemas → calls the service → answers.
"""
Invitations (B4, issue #141). Contract in `schemas.py`.

    POST   /api/invitations                        admin  → code and link (201)
    GET    /api/invitations                        admin  → list
    DELETE /api/invitations/{id}                   admin  → revoke (204)
    POST   /api/invitations/{id}/resend            admin  → new code
    GET    /api/invitations/by-code/{code}         public → just enough for the form
    POST   /api/invitations/by-code/{code}/accept  public → creates the user and opens a session (201)

The admin routes carry `require_role` one by one, not on the router,
because the two public ones hang from the same prefix. Those two are the
ones the gateway rate-limits per IP (`location /api/invitations/by-code/`).
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
# A `token_urlsafe` code has 24 characters; the cap only stops anything
# arbitrary from reaching the database.
Code = Annotated[str, Path(min_length=1, max_length=64)]

_SOLO_ADMIN = {
    **error_response(status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."),
    **error_response(
        status.HTTP_403_FORBIDDEN, "The session is not an admin one (`FORBIDDEN`)."
    ),
}
_NO_EXISTE = error_response(
    status.HTTP_404_NOT_FOUND, "The invitation does not exist (`INVITATION_NOT_FOUND`)."
)
_ENLACE = {
    **error_response(
        status.HTTP_404_NOT_FOUND,
        "The code does not exist, was already used or was revoked (`INVITATION_NOT_FOUND`).",
    ),
    **error_response(
        status.HTTP_410_GONE, "The invitation has expired (`INVITATION_EXPIRED`)."
    ),
}


# ---------------------------------------------------------
# ADMIN
# ---------------------------------------------------------
@router.post(
    "",
    response_model=InvitationSentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite an email",
    description=(
        "Creates an invitation to the organization, valid for "
        "`INVITATION_TTL_DAYS` days (7 by default).\n\n"
        "**`code` and `url` only show in this response**: the database "
        "stores their hash. The link is not emailed; the admin passes it "
        "on."
    ),
    responses={
        **_SOLO_ADMIN,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "The organization does not exist (`ORGANIZATION_NOT_FOUND`).",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "That email already has an account (`EMAIL_ALREADY_EXISTS`) or a "
            "valid invitation in that organization (`INVITATION_ALREADY_PENDING`).",
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
    summary="List invitations",
    description=(
        "Newest first, without the code. `status=PENDING` keeps the ones "
        "that can still be accepted."
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
        Query(alias="status", description="Keeps only the invitations in that status."),
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
    summary="Revoke an invitation",
    description="The link stops working. Revoking twice is not an error.",
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT, "It was already accepted (`INVITATION_NOT_PENDING`)."
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
    summary="Resend an invitation",
    description=(
        "New code and another `INVITATION_TTL_DAYS` days. The previous "
        "link stops working. It also works for an expired one."
    ),
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT,
            "It was already accepted or revoked (`INVITATION_NOT_PENDING`).",
        ),
    },
)
def resend_invitation(
    invitation_id: UUID, service: InvitationSvc, _admin: Admin
) -> InvitationSentResponse:
    return service.resend(invitation_id)


# ---------------------------------------------------------
# PUBLIC
# ---------------------------------------------------------
@router.get(
    "/by-code/{code}",
    response_model=InvitationPublicResponse,
    summary="Open an invitation link",
    description="No session. Just enough for the accept form.",
    responses={**_ENLACE},
)
def get_invitation_by_code(code: Code, service: InvitationSvc) -> InvitationPublicResponse:
    return service.get_by_code(code)


@router.post(
    "/by-code/{code}/accept",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Accept an invitation",
    description=(
        "No session. Creates the client account in the invitation's "
        "organization, with its email, and **leaves the session open**, "
        "like the sign-up. The link does not work again."
    ),
    responses={
        **_ENLACE,
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "The organization is suspended (`ACCOUNT_DISABLED`).",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "That email already has an account (`EMAIL_ALREADY_EXISTS`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Terms not accepted (`TERMS_NOT_ACCEPTED`), weak password "
            "(`WEAK_PASSWORD`) or empty name (`VALIDATION_ERROR`).",
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

    # As in login and sign-up: the router sets the cookie.
    response.set_cookie(
        SESSION_COOKIE,
        create_session_token(creado.id),
        max_age=SESSION_MAX_AGE_SECONDS,
        **session_cookie_kwargs(),
    )
    return SessionResponse(user=creado)
