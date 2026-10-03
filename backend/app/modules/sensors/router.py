# ROUTER — sensors
# Capa HTTP fina: valida schemas → llama service → responde.
# Sensores, umbrales y estado (vía site → organization).
"""
Endpoints de sensores (`/api/sensors/...`).

Registrado desde la issue #22, **sin rutas todavía**. Las del nivel
Básico se reparten en dos issues:

    GET   /api/sensors              → issue #25
    GET   /api/sensors/{id}         → issue #25
    POST  /api/sensors              → issue #29
    PATCH /api/sensors/{id}         → issue #29

`GET /api/sensors/{id}/readings` no irá aquí aunque su ruta empiece por
`/sensors`: pertenece al router de readings, que es quien tiene el
service y los schemas de lecturas. La ruta se compone igual desde
cualquiera de los dos; lo que decide dónde ponerla es de qué módulo es la
lógica.

`SensorResponse`, `SensorCreate`, `SensorUpdate` y `Page[SensorResponse]`
ya están publicados en la sección *Schemas* de Swagger.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.modules.sensors.schemas import SensorCreate, SensorResponse, SensorUpdate
from app.modules.sensors.service import SensorService, get_sensor_service
from app.shared.dependencies import OrgScope, Pagination, require_role
from app.shared.schemas import Page, error_response

router = APIRouter(prefix="/sensors", tags=["Sensors"])

SensorSvc = Annotated[SensorService, Depends(get_sensor_service)]

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
    response_model=Page[SensorResponse],
    summary="Listar sensores",
    description=(
        "Sensores de tu organización, paginados y ordenados por nombre. Un "
        "admin ve los de todas las organizaciones.\n\n"
        "`status` y `last_seen_at` se calculan a partir de las lecturas: un "
        "sensor está `OFFLINE` si lleva más de 5 minutos sin mandar ninguna "
        "o no ha mandado nunca."
    ),
    responses={**_NO_AUTORIZADO},
)
def list_sensors(
    service: SensorSvc, scope: OrgScope, pagination: Pagination
) -> Page[SensorResponse]:
    # La organización sale de la sesión (`OrgScope`), nunca de la query.
    return service.list(
        organization_id=scope,
        offset=pagination.offset,
        limit=pagination.limit,
    )


@router.get(
    "/{sensor_id}",
    response_model=SensorResponse,
    summary="Ver un sensor",
    responses={
        **_NO_AUTORIZADO,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "El sensor no existe, o no es de tu organización "
            "(`SENSOR_NOT_FOUND`).",
        ),
    },
)
def get_sensor(sensor_id: UUID, service: SensorSvc, scope: OrgScope) -> SensorResponse:
    return service.get(sensor_id, organization_id=scope)


_SOLO_ADMIN = {
    **error_response(status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."),
    **error_response(status.HTTP_403_FORBIDDEN, "La sesión no es de un admin (`FORBIDDEN`)."),
}


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Dar de alta un sensor",
    description=(
        "Solo admin. `external_id` es la etiqueta del aparato físico y no se "
        "puede repetir en el mismo site. `unit` vale `bar` si no se envía. "
        "El sensor nace `OFFLINE`: todavía no ha mandado lecturas."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **error_response(status.HTTP_404_NOT_FOUND, "El site no existe (`SITE_NOT_FOUND`)."),
        **error_response(
            status.HTTP_409_CONFLICT,
            "Ese `external_id` ya existe en el site (`SENSOR_EXTERNAL_ID_TAKEN`).",
        ),
    },
)
def create_sensor(payload: SensorCreate, service: SensorSvc) -> SensorResponse:
    return service.create(payload)


@router.patch(
    "/{sensor_id}",
    response_model=SensorResponse,
    summary="Modificar un sensor",
    description=(
        "Solo admin. Cambia solo los campos enviados: nombre, ubicación y "
        "umbrales. Si llega un solo umbral, se compara con el guardado."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **error_response(status.HTTP_404_NOT_FOUND, "El sensor no existe (`SENSOR_NOT_FOUND`)."),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Umbrales incoherentes o vacíos (`INVALID_THRESHOLDS`), o nombre vacío.",
        ),
    },
)
def update_sensor(
    sensor_id: UUID, payload: SensorUpdate, service: SensorSvc
) -> SensorResponse:
    return service.update(sensor_id, payload)
