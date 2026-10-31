# ROUTER — organizations
# Thin HTTP layer: validates schemas → calls the service → answers.
"""
Organization endpoints (`/api/organizations/...`). B1, issue #139;
includes #121.

    GET   /api/organizations                    → list with counters
    POST  /api/organizations                    → create (+ first_site)
    GET   /api/organizations/{id}               → detail
    PATCH /api/organizations/{id}               → name, contact, billing
    POST  /api/organizations/{id}/suspend       → its users can no longer log in
    POST  /api/organizations/{id}/reactivate    → back to TRIAL or ACTIVE
    POST  /api/organizations/{id}/extend-trial  → TRIAL_DAYS more of trial
    DELETE /api/organizations/{id}              → deletes everything (B16, issue #145)

**They are all admin only**, which is why `require_role` goes on the
whole router and not route by route: a new route cannot forget it.
Without a session it answers 401; with a client session, 403.

Status changes are a `POST` to an action and not a `PATCH` of the
`status` field, for the same reason as acknowledging and resolving
alerts: each change has its own rules and its own error, and an editable
field would hide them.
"""

from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationDelete,
    OrganizationDeleted,
    OrganizationResponse,
    OrganizationSort,
    OrganizationUpdate,
)
from app.modules.organizations.service import (
    OrganizationService,
    get_organization_service,
)
from app.shared.dependencies import Pagination, Search, require_role
from app.shared.enums import OrganizationStatus
from app.shared.schemas import Page, error_response

router = APIRouter(
    prefix="/organizations",
    tags=["Organizations"],
    dependencies=[Depends(require_role("admin"))],
)

OrganizationSvc = Annotated[OrganizationService, Depends(get_organization_service)]

_SOLO_ADMIN = {
    **error_response(status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."),
    **error_response(
        status.HTTP_403_FORBIDDEN, "The session is not an admin one (`FORBIDDEN`)."
    ),
}
_NO_EXISTE = error_response(
    status.HTTP_404_NOT_FOUND,
    "The organization does not exist (`ORGANIZATION_NOT_FOUND`).",
)
_NOMBRE = {
    **error_response(
        status.HTTP_409_CONFLICT,
        "There is already an organization with that name, ignoring case "
        "(`ORGANIZATION_NAME_TAKEN`).",
    ),
    **error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Empty name or with signs not allowed (`INVALID_NAME`), phone that is not "
        "Spanish (`INVALID_PHONE`), invalid tax id (`INVALID_TAX_ID`), "
        "text too long or malformed email (`VALIDATION_ERROR`).",
    ),
}


@router.get(
    "",
    response_model=Page[OrganizationResponse],
    summary="List organizations",
    description=(
        "Clients with their counters: buildings, sensors, users and open "
        "alerts (and how many are critical).\n\n"
        "`q` searches the name, the city, the legal name and the tax id. "
        "`has_open_alerts=true` keeps only those with some unresolved "
        "alert, the \"clients that need attention\" view.\n\n"
        "`sort` and `order` sort by name (default), trial end or any of "
        "the counters. Ties go by name, and clients without a trial end "
        "date always come last."
    ),
    responses={**_SOLO_ADMIN},
)
def list_organizations(
    service: OrganizationSvc,
    pagination: Pagination,
    q: Search,
    status_filtro: Annotated[
        OrganizationStatus | None,
        Query(alias="status", description="Keeps only the organizations in that status."),
    ] = None,
    has_open_alerts: Annotated[
        bool | None,
        Query(description="true: only with unresolved alerts. false: only without any."),
    ] = None,
    sort: Annotated[
        OrganizationSort, Query(description="Field to sort by.")
    ] = "name",
    order: Annotated[
        Literal["asc", "desc"], Query(description="`desc`: from highest to lowest.")
    ] = "asc",
) -> Page[OrganizationResponse]:
    return service.list(
        offset=pagination.offset,
        limit=pagination.limit,
        q=q,
        status=status_filtro,
        has_open_alerts=has_open_alerts,
        sort=sort,
        descending=order == "desc",
    )


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an organization",
    description=(
        "Creates a client on trial (`TRIAL`, expiring in `TRIAL_DAYS`). "
        "With `first_site`, it also creates its first building in the same "
        "operation.\n\n"
        "Users are not created here: they arrive by invitation (B4)."
    ),
    responses={**_SOLO_ADMIN, **_NOMBRE},
)
def create_organization(
    payload: OrganizationCreate, service: OrganizationSvc
) -> OrganizationResponse:
    return service.create(payload)


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get an organization",
    description=(
        "The client detail with its counters. Its buildings are requested "
        "separately with `GET /api/sites?organization_id=...`."
    ),
    responses={**_SOLO_ADMIN, **_NO_EXISTE},
)
def get_organization(
    organization_id: UUID, service: OrganizationSvc
) -> OrganizationResponse:
    return service.get(organization_id)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update an organization",
    description=(
        "Changes only the fields sent: name, contact and billing. The "
        "status is changed with the actions below."
    ),
    responses={**_SOLO_ADMIN, **_NO_EXISTE, **_NOMBRE},
)
def update_organization(
    organization_id: UUID, payload: OrganizationUpdate, service: OrganizationSvc
) -> OrganizationResponse:
    return service.update(organization_id, payload)


@router.post(
    "/{organization_id}/suspend",
    response_model=OrganizationResponse,
    summary="Suspend an organization",
    description=(
        "Its users can no longer log in, including those who already had "
        "an open session. Nothing is deleted."
    ),
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT,
            "It was already suspended (`ORGANIZATION_ALREADY_SUSPENDED`).",
        ),
    },
)
def suspend_organization(
    organization_id: UUID, service: OrganizationSvc
) -> OrganizationResponse:
    return service.suspend(organization_id)


@router.post(
    "/{organization_id}/reactivate",
    response_model=OrganizationResponse,
    summary="Reactivate a suspended organization",
    description=(
        "Goes back to `TRIAL` if it was on trial (it keeps `trial_ends_at`) "
        "and to `ACTIVE` if it was a client."
    ),
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT,
            "It was not suspended (`ORGANIZATION_NOT_SUSPENDED`).",
        ),
    },
)
def reactivate_organization(
    organization_id: UUID, service: OrganizationSvc
) -> OrganizationResponse:
    return service.reactivate(organization_id)


_SOLO_EN_PRUEBA = error_response(
    status.HTTP_409_CONFLICT,
    "The organization is not on trial (`ORGANIZATION_NOT_IN_TRIAL`).",
)


@router.post(
    "/{organization_id}/extend-trial",
    response_model=OrganizationResponse,
    summary="Extend the trial",
    description=(
        "Adds `TRIAL_DAYS` (7 by default) to the end of the trial. If it had "
        "already expired, they count from today."
    ),
    responses={**_SOLO_ADMIN, **_NO_EXISTE, **_SOLO_EN_PRUEBA},
)
def extend_trial(
    organization_id: UUID, service: OrganizationSvc
) -> OrganizationResponse:
    return service.extend_trial(organization_id)



@router.delete(
    "/{organization_id}",
    response_model=OrganizationDeleted,
    summary="Delete an organization with all its data",
    description=(
        "Deletes the organization, its buildings, sensors, readings, "
        "alerts, documents (their files too), invitations and users, in a "
        "single transaction: either everything is deleted or nothing. It "
        "cannot be undone; to keep a client out without losing data, use "
        "`/suspend`.\n\n"
        "`confirm_name` must be sent with the exact name of the "
        "organization. Admins that had it assigned are not deleted: they "
        "are left without an organization."
    ),
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "`confirm_name` does not match the name "
            "(`NAME_CONFIRMATION_MISMATCH`) or is missing (`VALIDATION_ERROR`).",
        ),
    },
)
def delete_organization(
    organization_id: UUID, payload: OrganizationDelete, service: OrganizationSvc
) -> OrganizationDeleted:
    return service.delete(organization_id, payload.confirm_name)
