# ROUTER — sensors
# Thin HTTP layer: validates schemas → calls the service → answers.
# Sensors, thresholds and status (via site → organization).
"""
Sensor endpoints (`/api/sensors/...`).

Implemented in two issues; the common filters come from B0 (#138), and
the floor, `health`, `last_value` and `?health=`, from B3 (#139):

    GET   /api/sensors              → issue #25 (PR #113)
    GET   /api/sensors/{id}         → issue #25 (PR #113)
    POST  /api/sensors              → issue #29 (PR #115)
    POST  /api/sensors/import       → import a CSV ("Data export and import")
    PATCH /api/sensors/{id}         → issue #29 (PR #115)

`GET /api/sensors/{id}/readings` is not here even though its route starts
with `/sensors`: it belongs to the readings router, which has the reading
service and schemas. The route is built the same from either; what
decides where it goes is which module owns the logic.
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
    Query(description="Keeps only the sensors with that health (`health`)."),
]

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
    response_model=Page[SensorResponse],
    summary="List sensors",
    description=(
        "Sensors of your organization, paginated and ordered by name. An "
        "admin sees those of every organization.\n\n"
        "`status`, `last_seen_at` and `last_value` are computed from the "
        "readings: a sensor is `OFFLINE` if it has gone more than 5 minutes "
        "without sending any or has never sent one. `health` adds its "
        "unresolved alerts: `OFFLINE`, otherwise `CRITICAL` or `WARNING`, "
        "and otherwise `OK`.\n\n"
        "`q` searches the name, the label (`external_id`) and the location. "
        "`organization_id` and `site_id` keep only those of one client or "
        "one building, and `health` those with that health."
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
    # The scope comes from the session (`OrgScope`), never from the query.
    # `organization_id`, `site_id` and `health` only narrow it.
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
    summary="Get a sensor",
    responses={
        **_NO_AUTORIZADO,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "The sensor does not exist, or is not from your organization "
            "(`SENSOR_NOT_FOUND`).",
        ),
    },
)
def get_sensor(sensor_id: UUID, service: SensorSvc, scope: OrgScope) -> SensorResponse:
    return service.get(sensor_id, organization_id=scope)


_SOLO_ADMIN = {
    **error_response(status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."),
    **error_response(status.HTTP_403_FORBIDDEN, "The session is not an admin one (`FORBIDDEN`)."),
}


@router.post(
    "",
    response_model=SensorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a sensor",
    description=(
        "Admin only. `external_id` is the label of the physical device and "
        "cannot repeat in the same site. `unit` is `bar` if not sent. "
        "`floor` (0 if not sent) must exist in the building: from "
        "`-basements` to `floors - 1`. "
        "The sensor starts `OFFLINE`: it has not sent readings yet."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **error_response(status.HTTP_404_NOT_FOUND, "The site does not exist (`SITE_NOT_FOUND`)."),
        **error_response(
            status.HTTP_409_CONFLICT,
            "That `external_id` already exists in the site (`SENSOR_EXTERNAL_ID_TAKEN`) "
            "or the client already has all its contracted sensors "
            "(`SENSOR_LIMIT_REACHED`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "The floor does not exist in the building (`FLOOR_OUT_OF_SITE`).",
        ),
    },
)
def create_sensor(payload: SensorCreate, service: SensorSvc) -> SensorResponse:
    return service.create(payload)


@router.post(
    "/import",
    response_model=SensorImportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import sensors from a CSV",
    description=(
        "Admin only. Creates every sensor of a CSV in a building, with the "
        "same rules as `POST /api/sensors`. **All or nothing**: if one row "
        "fails none is created, and `details` lists each error with its "
        "line (`row`, the header is line 1), its `field` and its "
        "`message`.\n\n"
        "Required columns: `external_id`, `name`, `min_pressure` and "
        "`max_pressure`; optional: `location` and `floor` (0 if missing). "
        "`;` or `,` separator, UTF-8 or Windows-1252, decimals with a comma "
        f"or a point. At most {MAX_IMPORT_ROWS} sensors per file.\n\n"
        "With `dry_run=true` it validates the same and creates nothing "
        "(200): it is the preview before confirming."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **error_response(status.HTTP_404_NOT_FOUND, "The site does not exist (`SITE_NOT_FOUND`)."),
        **error_response(
            status.HTTP_409_CONFLICT,
            "These sensors would go over the contracted ones (`SENSOR_LIMIT_REACHED`), "
            "or another creation used one of the labels at the same time "
            "(`SENSOR_EXTERNAL_ID_TAKEN`).",
        ),
        **error_response(
            status.HTTP_413_CONTENT_TOO_LARGE, "The file is too large (`FILE_TOO_LARGE`)."
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Rows with errors (`IMPORT_INVALID_ROWS`, one per row and field in "
            "`details`), or the whole file is not valid: empty (`EMPTY_FILE`), "
            "not text (`UNSUPPORTED_FILE_TYPE`), missing columns "
            "(`IMPORT_MISSING_COLUMNS`), no rows (`IMPORT_NO_ROWS`) or "
            f"more than {MAX_IMPORT_ROWS} (`IMPORT_TOO_MANY_ROWS`).",
        ),
    },
)
def import_sensors(
    service: SensorSvc,
    response: Response,
    file: Annotated[UploadFile, File(description="The CSV with the sensors.")],
    site_id: Annotated[UUID, Form(description="Building where they are installed.")],
    dry_run: Annotated[
        bool, Form(description="true: only validates and returns the preview.")
    ] = False,
) -> SensorImportResponse:
    resultado = service.import_csv(site_id=site_id, source=file.file, dry_run=dry_run)
    if dry_run:
        response.status_code = status.HTTP_200_OK
    return resultado


@router.patch(
    "/{sensor_id}",
    response_model=SensorResponse,
    summary="Update a sensor",
    description=(
        "Admin only. Changes only the fields sent: name, location, "
        "thresholds and floor. If only one threshold arrives, it is "
        "compared with the stored one. The floor must exist in the "
        "building."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **_SOLO_ADMIN,
        **error_response(status.HTTP_404_NOT_FOUND, "The sensor does not exist (`SENSOR_NOT_FOUND`)."),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Inconsistent or empty thresholds (`INVALID_THRESHOLDS`), empty "
            "name or floor, or a floor that does not exist in the building "
            "(`FLOOR_OUT_OF_SITE`).",
        ),
    },
)
def update_sensor(
    sensor_id: UUID, payload: SensorUpdate, service: SensorSvc
) -> SensorResponse:
    return service.update(sensor_id, payload)
