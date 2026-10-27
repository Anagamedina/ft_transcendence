# ROUTER — sensors
# Capa HTTP fina: valida schemas → llama service → responde.
# Sensores, umbrales y estado (vía site → organization).
"""
Endpoints de sensores (`/api/sensors/...`).

Implementados en dos issues; los filtros comunes son de la B0 (#138), y
la planta, `health`, `last_value` y `?health=`, de la B3 (#139):

    GET   /api/sensors              → issue #25 (PR #113)
    GET   /api/sensors/{id}         → issue #25 (PR #113)
    POST  /api/sensors              → issue #29 (PR #115)
    POST  /api/sensors/import       → importar un CSV («Data export and import»)
    PATCH /api/sensors/{id}         → issue #29 (PR #115)

`GET /api/sensors/{id}/readings` no está aquí aunque su ruta empiece por
`/sensors`: pertenece al router de readings, que es quien tiene el
service y los schemas de lecturas. La ruta se compone igual desde
cualquiera de los dos; lo que decide dónde ponerla es de qué módulo es la
lógica.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status

from app.modules.sensors.importer import MAX_IMPORT_ROWS
from app.modules.sensors.schemas import (
    SensorCreate,
    SensorImportResponse,
    SensorResponse,
    SensorUpdate,
)
from app.modules.sensors.service import SensorService, get_sensor_service
from app.shared.dependencies import (
    OrganizationIdFilter,
    OrgScope,
    Pagination,
    Search,
    SiteIdFilter,
    require_role,
)
from app.shared.enums import SensorHealth
from app.shared.schemas import Page, error_response

router = APIRouter(prefix="/sensors", tags=["Sensors"])

SensorSvc = Annotated[SensorService, Depends(get_sensor_service)]

HealthFilter = Annotated[
    SensorHealth | None,
    Query(description="Deja solo los sensores con esa salud (`health`)."),
]

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
        "`status`, `last_seen_at` y `last_value` se calculan a partir de las "
        "lecturas: un sensor está `OFFLINE` si lleva más de 5 minutos sin "
        "mandar ninguna o no ha mandado nunca. `health` añade sus alertas "
        "sin resolver: `OFFLINE`, si no `CRITICAL` o `WARNING`, y si no `OK`.\n\n"
        "`q` busca en el nombre, la etiqueta (`external_id`) y la ubicación. "
        "`organization_id` y `site_id` dejan solo los de un cliente o un "
        "edificio, y `health` los que tienen esa salud."
    ),
    responses={**_NO_AUTORIZADO},
)
def list_sensors(
    service: SensorSvc,
    scope: OrgScope,
    pagination: Pagination,
    q: Search,
    organization_id: OrganizationIdFilter = None,
    site_id: SiteIdFilter = None,
    health: HealthFilter = None,
) -> Page[SensorResponse]:
    # El alcance sale de la sesión (`OrgScope`), nunca de la query.
    # `organization_id`, `site_id` y `health` solo lo estrechan.
    return service.list(
        organization_id=scope,
        offset=pagination.offset,
        limit=pagination.limit,
        q=q,
        organization_filter=organization_id,
        site_id=site_id,
        health=health,
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
        "`floor` (0 si no se envía) tiene que existir en el edificio: de "
        "`-basements` a `floors - 1`. "
        "El sensor nace `OFFLINE`: todavía no ha mandado lecturas."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **error_response(status.HTTP_404_NOT_FOUND, "El site no existe (`SITE_NOT_FOUND`)."),
        **error_response(
            status.HTTP_409_CONFLICT,
            "Ese `external_id` ya existe en el site (`SENSOR_EXTERNAL_ID_TAKEN`) "
            "o el cliente ya tiene todos sus sensores contratados "
            "(`SENSOR_LIMIT_REACHED`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "La planta no existe en el edificio (`FLOOR_OUT_OF_SITE`).",
        ),
    },
)
def create_sensor(payload: SensorCreate, service: SensorSvc) -> SensorResponse:
    return service.create(payload)


@router.post(
    "/import",
    response_model=SensorImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Importar sensores desde un CSV",
    description=(
        "Solo admin. Da de alta todos los sensores de un CSV en un edificio, "
        "con las mismas reglas que `POST /api/sensors`. **Todo o nada**: si "
        "una fila falla no se crea ninguno, y `details` lista cada error con "
        "su línea (`row`, la cabecera es la 1), su `field` y su `message`.\n\n"
        "Columnas obligatorias: `external_id`, `name`, `min_pressure` y "
        "`max_pressure`; opcionales: `location` y `floor` (0 si falta). "
        "Separador `;` o `,`, UTF-8 o Windows-1252, decimales con coma o "
        f"punto. Como mucho {MAX_IMPORT_ROWS} sensores por archivo.\n\n"
        "Con `dry_run=true` valida igual y no crea nada (200): es la vista "
        "previa antes de confirmar."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **error_response(status.HTTP_404_NOT_FOUND, "El site no existe (`SITE_NOT_FOUND`)."),
        **error_response(
            status.HTTP_409_CONFLICT,
            "Con estos sensores pasaría de los contratados (`SENSOR_LIMIT_REACHED`), "
            "u otra alta ha usado a la vez una de las etiquetas "
            "(`SENSOR_EXTERNAL_ID_TAKEN`).",
        ),
        **error_response(
            status.HTTP_413_CONTENT_TOO_LARGE, "El archivo es demasiado grande (`FILE_TOO_LARGE`)."
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Filas con errores (`IMPORT_INVALID_ROWS`, uno por fila y campo en "
            "`details`), o el archivo entero no vale: vacío (`EMPTY_FILE`), "
            "no es texto (`UNSUPPORTED_FILE_TYPE`), le faltan columnas "
            "(`IMPORT_MISSING_COLUMNS`), no tiene filas (`IMPORT_NO_ROWS`) o "
            f"tiene más de {MAX_IMPORT_ROWS} (`IMPORT_TOO_MANY_ROWS`).",
        ),
    },
)
def import_sensors(
    service: SensorSvc,
    response: Response,
    file: Annotated[UploadFile, File(description="El CSV con los sensores.")],
    site_id: Annotated[UUID, Form(description="Edificio donde se instalan.")],
    dry_run: Annotated[
        bool, Form(description="true: solo valida y devuelve la vista previa.")
    ] = False,
) -> SensorImportResponse:
    resultado = service.import_csv(site_id=site_id, source=file.file, dry_run=dry_run)
    if dry_run:
        response.status_code = status.HTTP_200_OK
    return resultado


@router.patch(
    "/{sensor_id}",
    response_model=SensorResponse,
    summary="Modificar un sensor",
    description=(
        "Solo admin. Cambia solo los campos enviados: nombre, ubicación, "
        "umbrales y planta. Si llega un solo umbral, se compara con el "
        "guardado. La planta tiene que existir en el edificio."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **error_response(status.HTTP_404_NOT_FOUND, "El sensor no existe (`SENSOR_NOT_FOUND`)."),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Umbrales incoherentes o vacíos (`INVALID_THRESHOLDS`), nombre o "
            "planta vacíos, o planta que no existe en el edificio "
            "(`FLOOR_OUT_OF_SITE`).",
        ),
    },
)
def update_sensor(
    sensor_id: UUID, payload: SensorUpdate, service: SensorSvc
) -> SensorResponse:
    return service.update(sensor_id, payload)
