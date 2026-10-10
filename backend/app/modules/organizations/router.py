# ROUTER — organizations
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de organizaciones (`/api/organizations/...`). B1, issue #139;
incluye la #121.

    GET   /api/organizations                    → lista con contadores
    POST  /api/organizations                    → alta (+ first_site)
    GET   /api/organizations/{id}               → ficha
    PATCH /api/organizations/{id}               → nombre, contacto, facturación
    POST  /api/organizations/{id}/suspend       → sus usuarios dejan de entrar
    POST  /api/organizations/{id}/reactivate    → vuelve a TRIAL o ACTIVE
    POST  /api/organizations/{id}/extend-trial  → TRIAL_DAYS más de prueba
    POST  /api/organizations/{id}/activate      → la prueba pasa a cliente

**Todas son solo de admin**, y por eso el `require_role` va en el router
entero y no ruta a ruta: así una ruta nueva no puede olvidarlo. Sin sesión
responde 401; con sesión de cliente, 403.

Los cambios de estado son `POST` a una acción y no un `PATCH` del campo
`status`, por lo mismo que reconocer y resolver alertas: cada cambio tiene
sus reglas y su error propio, y un campo editable los escondería.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.organizations.schemas import (
    OrganizationCreate,
    OrganizationResponse,
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
    **error_response(status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."),
    **error_response(
        status.HTTP_403_FORBIDDEN, "La sesión no es de un admin (`FORBIDDEN`)."
    ),
}
_NO_EXISTE = error_response(
    status.HTTP_404_NOT_FOUND,
    "La organización no existe (`ORGANIZATION_NOT_FOUND`).",
)
_NOMBRE = {
    **error_response(
        status.HTTP_409_CONFLICT,
        "Ya hay una organización con ese nombre, sin distinguir mayúsculas "
        "(`ORGANIZATION_NAME_TAKEN`).",
    ),
    **error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT,
        "Nombre vacío (`INVALID_NAME`), demasiado largo o email mal escrito "
        "(`VALIDATION_ERROR`).",
    ),
}


@router.get(
    "",
    response_model=Page[OrganizationResponse],
    summary="Listar organizaciones",
    description=(
        "Clientes por nombre, con sus contadores: edificios, sensores, "
        "usuarios y alertas abiertas (y cuántas son críticas).\n\n"
        "`q` busca en el nombre, la ciudad, la razón social y el NIF. "
        "`has_open_alerts=true` deja solo los que tienen alguna alerta sin "
        "resolver, que es la vista «clientes que necesitan atención»."
    ),
    responses={**_SOLO_ADMIN},
)
def list_organizations(
    service: OrganizationSvc,
    pagination: Pagination,
    q: Search,
    status_filtro: Annotated[
        OrganizationStatus | None,
        Query(alias="status", description="Deja solo las organizaciones en ese estado."),
    ] = None,
    has_open_alerts: Annotated[
        bool | None,
        Query(description="true: solo con alertas sin resolver. false: solo sin ninguna."),
    ] = None,
) -> Page[OrganizationResponse]:
    return service.list(
        offset=pagination.offset,
        limit=pagination.limit,
        q=q,
        status=status_filtro,
        has_open_alerts=has_open_alerts,
    )


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta una organización",
    description=(
        "Crea un cliente `ACTIVE`. Con `first_site`, crea también su primer "
        "edificio en la misma operación.\n\n"
        "Los usuarios no se crean aquí: llegan por invitación (B4)."
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
    summary="Ver una organización",
    description=(
        "La ficha del cliente con sus contadores. Sus edificios se piden "
        "aparte con `GET /api/sites?organization_id=...`."
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
    summary="Modificar una organización",
    description=(
        "Cambia solo los campos enviados: nombre, contacto y facturación. "
        "El estado se cambia con las acciones de abajo."
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
    summary="Suspender una organización",
    description=(
        "Sus usuarios dejan de poder entrar, también los que ya tenían la "
        "sesión abierta. No se borra nada."
    ),
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT,
            "Ya estaba suspendida (`ORGANIZATION_ALREADY_SUSPENDED`).",
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
    summary="Reactivar una organización suspendida",
    description=(
        "Vuelve a `TRIAL` si estaba en prueba (conserva `trial_ends_at`) y a "
        "`ACTIVE` si era cliente."
    ),
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_409_CONFLICT,
            "No estaba suspendida (`ORGANIZATION_NOT_SUSPENDED`).",
        ),
    },
)
def reactivate_organization(
    organization_id: UUID, service: OrganizationSvc
) -> OrganizationResponse:
    return service.reactivate(organization_id)


_SOLO_EN_PRUEBA = error_response(
    status.HTTP_409_CONFLICT,
    "La organización no está en prueba (`ORGANIZATION_NOT_IN_TRIAL`).",
)


@router.post(
    "/{organization_id}/extend-trial",
    response_model=OrganizationResponse,
    summary="Ampliar la prueba",
    description=(
        "Suma `TRIAL_DAYS` (7 por defecto) al fin de la prueba. Si ya había "
        "caducado, se cuentan desde hoy."
    ),
    responses={**_SOLO_ADMIN, **_NO_EXISTE, **_SOLO_EN_PRUEBA},
)
def extend_trial(
    organization_id: UUID, service: OrganizationSvc
) -> OrganizationResponse:
    return service.extend_trial(organization_id)


@router.post(
    "/{organization_id}/activate",
    response_model=OrganizationResponse,
    summary="Pasar la prueba a cliente",
    description="De `TRIAL` a `ACTIVE`. Se borra el fin de la prueba.",
    responses={**_SOLO_ADMIN, **_NO_EXISTE, **_SOLO_EN_PRUEBA},
)
def activate_organization(
    organization_id: UUID, service: OrganizationSvc
) -> OrganizationResponse:
    return service.activate(organization_id)
