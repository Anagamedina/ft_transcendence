# ROUTER — sites
# Thin HTTP layer: validates schemas → calls the service → answers.
"""
Site endpoints (`/api/sites/...`).

Read in issue #29 (PR #108), common filters in B0 (#138), and create,
edit and delete in B2 (#139):

    GET    /api/sites                → with a session (each one sees their own)
    GET    /api/sites/{id}           → with a session
    GET    /api/sites/{id}/sensors   → with a session
    POST   /api/sites                → admin only
    PATCH  /api/sites/{id}           → admin only
    DELETE /api/sites/{id}           → admin only, if it has no sensors or documents
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from app.modules.sensors.schemas import SensorResponse
from app.modules.sites.schemas import SiteCreate, SiteResponse, SiteUpdate
from app.modules.sites.service import SiteService, get_site_service
from app.shared.dependencies import (
    OrganizationIdFilter,
    OrgScope,
    Pagination,
    Search,
    require_role,
)
from app.shared.schemas import Page, error_response

router = APIRouter(prefix="/sites", tags=["Sites"])

SiteSvc = Annotated[SiteService, Depends(get_site_service)]

_NO_AUTORIZADO = {
    **error_response(
        status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."
    ),
    **error_response(
        status.HTTP_403_FORBIDDEN,
        "Client account without an organization (`FORBIDDEN`).",
    ),
}


@router.get(
    "",
    response_model=Page[SiteResponse],
    summary="List sites",
    description=(
        "Sites of your organization, paginated and ordered by name. An "
        "admin sees those of every organization.\n\n"
        "Each site brings `sensor_count` and `status`: `CRITICAL` or "
        "`WARNING` depending on its open alerts, `OK` if it has none.\n\n"
        "`q` searches the name and the address. `organization_id` keeps "
        "only those of one client (useful for the admin)."
    ),
    responses={**_NO_AUTORIZADO},
)
def list_sites(
    service: SiteSvc,
    scope: OrgScope,
    pagination: Pagination,
    q: Search,
    organization_id: OrganizationIdFilter = None,
) -> Page[SiteResponse]:
    # The scope comes from the session (`OrgScope`), never from the query.
    # `organization_id` only narrows that scope, it never widens it.
    return service.list(
        organization_id=scope,
        offset=pagination.offset,
        limit=pagination.limit,
        q=q,
        organization_filter=organization_id,
    )


@router.get(
    "/{site_id}",
    response_model=SiteResponse,
    summary="Get a site",
    responses={
        **_NO_AUTORIZADO,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "The site does not exist, or is not from your organization (`SITE_NOT_FOUND`).",
        ),
    },
)
def get_site(site_id: UUID, service: SiteSvc, scope: OrgScope) -> SiteResponse:
    return service.get(site_id, organization_id=scope)


@router.get(
    "/{site_id}/sensors",
    response_model=Page[SensorResponse],
    summary="Sensors of a site",
    description=(
        "Sensors installed in the site, paginated and by name, with the same "
        "format as `GET /api/sensors` (status and last reading included)."
    ),
    responses={
        **_NO_AUTORIZADO,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "The site does not exist, or is not from your organization (`SITE_NOT_FOUND`).",
        ),
    },
)
def list_site_sensors(
    site_id: UUID, service: SiteSvc, scope: OrgScope, pagination: Pagination
) -> Page[SensorResponse]:
    return service.list_sensors(
        site_id,
        organization_id=scope,
        offset=pagination.offset,
        limit=pagination.limit,
    )


_SOLO_ADMIN = {
    **error_response(status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."),
    **error_response(
        status.HTTP_403_FORBIDDEN, "The session is not an admin one (`FORBIDDEN`)."
    ),
}
_NO_EXISTE = error_response(
    status.HTTP_404_NOT_FOUND, "The site does not exist (`SITE_NOT_FOUND`)."
)
_NOMBRE_OCUPADO = error_response(
    status.HTTP_409_CONFLICT,
    "That client already has a building with that name (`SITE_NAME_TAKEN`).",
)


@router.post(
    "",
    response_model=SiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a site",
    description=(
        "Admin only. Creates a building in the client `organization_id`, "
        "with its floors (`floors`, counting the ground floor), basements "
        "and type.\n\n"
        "It respects the building limit: 1 on trial and the plan one for a "
        "client (B14)."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "The organization does not exist (`ORGANIZATION_NOT_FOUND`).",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "That client already has a building with that name (`SITE_NAME_TAKEN`) "
            "or has reached its building limit (`SITE_LIMIT_REACHED`).",
        ),
    },
)
def create_site(payload: SiteCreate, service: SiteSvc) -> SiteResponse:
    return service.create(payload)


@router.patch(
    "/{site_id}",
    response_model=SiteResponse,
    summary="Update a site",
    description=(
        "Admin only. Changes only the fields sent. The client cannot be "
        "changed. Removing floors or basements that have sensors answers "
        "422 `FLOOR_OUT_OF_SITE`."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **_NOMBRE_OCUPADO,
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Sensors would be left outside the building (`FLOOR_OUT_OF_SITE`), "
            "or a mandatory field is empty.",
        ),
    },
)
def update_site(site_id: UUID, payload: SiteUpdate, service: SiteSvc) -> SiteResponse:
    return service.update(site_id, payload)


@router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a site",
    description=(
        "Admin only, and only if the building is empty: with sensors their "
        "readings and alerts would be lost, and with documents, the "
        "documents and their files."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT,
            "The building has sensors (`SITE_HAS_SENSORS`) or documents "
            "(`SITE_HAS_DOCUMENTS`).",
        ),
    },
)
def delete_site(site_id: UUID, service: SiteSvc) -> Response:
    service.delete(site_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
