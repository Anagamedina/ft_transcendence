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
    DELETE /api/organizations/{id}              → borra todo (B16, issue #145)

**Todas son solo de admin**, y por eso el `require_role` va en el router
entero y no ruta a ruta: así una ruta nueva no puede olvidarlo. Sin sesión
responde 401; con sesión de cliente, 403.

Los cambios de estado son `POST` a una acción y no un `PATCH` del campo
`status`, por lo mismo que reconocer y resolver alertas: cada cambio tiene
sus reglas y su error propio, y un campo editable los escondería.
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
        "Clientes con sus contadores: edificios, sensores, usuarios y "
        "alertas abiertas (y cuántas son críticas).\n\n"
        "`q` busca en el nombre, la ciudad, la razón social y el NIF. "
        "`has_open_alerts=true` deja solo los que tienen alguna alerta sin "
        "resolver, que es la vista «clientes que necesitan atención».\n\n"
        "`sort` y `order` ordenan por nombre (por defecto), fin de la prueba "
        "o cualquiera de los contadores. Los empates van por nombre, y los "
        "clientes sin fecha de fin de prueba salen siempre al final."
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
    sort: Annotated[
        OrganizationSort, Query(description="Campo por el que se ordena.")
    ] = "name",
    order: Annotated[
        Literal["asc", "desc"], Query(description="`desc`: de mayor a menor.")
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



@router.delete(
    "/{organization_id}",
    response_model=OrganizationDeleted,
    summary="Eliminar una organización con todos sus datos",
    description=(
        "Borra la organización, sus edificios, sensores, lecturas, alertas, "
        "documentos (también sus archivos), invitaciones y usuarios, en una "
        "sola transacción: o se borra todo o nada. No se puede deshacer; "
        "para dejar a un cliente fuera sin perder datos, `/suspend`.\n\n"
        "Hay que enviar `confirm_name` con el nombre exacto de la "
        "organización. Los admins que la tuvieran asignada no se borran: se "
        "quedan sin organización."
    ),
    responses={
        **_SOLO_ADMIN,
        **_NO_EXISTE,
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "`confirm_name` no coincide con el nombre "
            "(`NAME_CONFIRMATION_MISMATCH`) o falta (`VALIDATION_ERROR`).",
        ),
    },
)
def delete_organization(
    organization_id: UUID, payload: OrganizationDelete, service: OrganizationSvc
) -> OrganizationDeleted:
    return service.delete(organization_id, payload.confirm_name)
