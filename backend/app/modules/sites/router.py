# ROUTER — sites
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de emplazamientos (`/api/sites/...`).

Lectura en la issue #29 (PR #108), filtros comunes en la B0 (#138), y
alta, edición y borrado en la B2 (#139):

    GET    /api/sites                → con sesión (cada uno ve lo suyo)
    GET    /api/sites/{id}           → con sesión
    GET    /api/sites/{id}/sensors   → con sesión
    POST   /api/sites                → solo admin
    PATCH  /api/sites/{id}           → solo admin
    DELETE /api/sites/{id}           → solo admin, si no tiene sensores ni documentos
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
        "Cada site trae `sensor_count` y `status`: `CRITICAL` o `WARNING` "
        "según sus alertas abiertas, `OK` si no tiene ninguna.\n\n"
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


_SOLO_ADMIN = {
    **error_response(status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."),
    **error_response(
        status.HTTP_403_FORBIDDEN, "La sesión no es de un admin (`FORBIDDEN`)."
    ),
}
_NO_EXISTE = error_response(
    status.HTTP_404_NOT_FOUND, "El site no existe (`SITE_NOT_FOUND`)."
)
_NOMBRE_OCUPADO = error_response(
    status.HTTP_409_CONFLICT,
    "Ese cliente ya tiene un edificio con ese nombre (`SITE_NAME_TAKEN`).",
)


@router.post(
    "",
    response_model=SiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta un site",
    description=(
        "Solo admin. Crea un edificio en el cliente `organization_id`, con sus "
        "plantas (`floors`, contando la baja), sótanos y tipo.\n\n"
        "Respeta el límite de edificios: 1 en prueba y el de su plan si es "
        "cliente (B14)."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "La organización no existe (`ORGANIZATION_NOT_FOUND`).",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "Ese cliente ya tiene un edificio con ese nombre (`SITE_NAME_TAKEN`) "
            "o ha llegado a su límite de edificios (`SITE_LIMIT_REACHED`).",
        ),
    },
)
def create_site(payload: SiteCreate, service: SiteSvc) -> SiteResponse:
    return service.create(payload)


@router.patch(
    "/{site_id}",
    response_model=SiteResponse,
    summary="Modificar un site",
    description=(
        "Solo admin. Cambia solo los campos enviados. No se puede cambiar de "
        "cliente. Quitar plantas o sótanos que tienen sensores responde 422 "
        "`FLOOR_OUT_OF_SITE`."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **_NOMBRE_OCUPADO,
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Quedarían sensores fuera del edificio (`FLOOR_OUT_OF_SITE`), o un "
            "campo obligatorio vacío.",
        ),
    },
)
def update_site(site_id: UUID, payload: SiteUpdate, service: SiteSvc) -> SiteResponse:
    return service.update(site_id, payload)


@router.delete(
    "/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un site",
    description=(
        "Solo admin, y solo si el edificio está vacío: con sensores se "
        "perderían sus lecturas y alertas, y con documentos, los documentos "
        "y sus ficheros."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT,
            "El edificio tiene sensores (`SITE_HAS_SENSORS`) o documentos "
            "(`SITE_HAS_DOCUMENTS`).",
        ),
    },
)
def delete_site(site_id: UUID, service: SiteSvc) -> Response:
    service.delete(site_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
