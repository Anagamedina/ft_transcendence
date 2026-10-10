# ROUTER — sites
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de emplazamientos (`/api/sites/...`).

Registrado desde la issue #22. Las del nivel Básico son de la issue #29;
las tres están hechas:

    GET /api/sites
    GET /api/sites/{id}
    GET /api/sites/{id}/sensors

`SiteResponse` y `Page[SiteResponse]` ya están publicados en la sección
*Schemas* de Swagger, que es lo que necesita Florinda para el mapa
Leaflet (issue #8) y Lylia para el `MockAdapter`.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.modules.sensors.schemas import SensorResponse
from app.modules.sites.schemas import SiteResponse
from app.modules.sites.service import SiteService, get_site_service
from app.shared.dependencies import (
    OrganizationIdFilter,
    OrgScope,
    Pagination,
    Search,
)
from app.shared.schemas import Page, error_response

router = APIRouter(prefix="/sites", tags=["Sites"])

SiteSvc = Annotated[SiteService, Depends(get_site_service)]

_NO_AUTORIZADO = {
    **error_response(
        status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."
    ),
    **error_response(
        status.HTTP_403_FORBIDDEN,
        "Cuenta de cliente sin organización (`FORBIDDEN`).",
    ),
}


@router.get(
    "",
    response_model=Page[SiteResponse],
    summary="Listar sites",
    description=(
        "Sites de tu organización, paginados y ordenados por nombre. Un "
        "admin ve los de todas las organizaciones.\n\n"
        "`q` busca en el nombre y la dirección. `organization_id` deja solo "
        "los de un cliente (útil para el admin)."
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
    # El alcance sale de la sesión (`OrgScope`), nunca de la query.
    # `organization_id` solo estrecha ese alcance, no lo amplía.
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
    summary="Ver un site",
    responses={
        **_NO_AUTORIZADO,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "El site no existe, o no es de tu organización (`SITE_NOT_FOUND`).",
        ),
    },
)
def get_site(site_id: UUID, service: SiteSvc, scope: OrgScope) -> SiteResponse:
    return service.get(site_id, organization_id=scope)


@router.get(
    "/{site_id}/sensors",
    response_model=Page[SensorResponse],
    summary="Sensores de un site",
    description=(
        "Sensores instalados en el site, paginados y por nombre, con el mismo "
        "formato que `GET /api/sensors` (estado y última lectura incluidos)."
    ),
    responses={
        **_NO_AUTORIZADO,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "El site no existe, o no es de tu organización (`SITE_NOT_FOUND`).",
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
