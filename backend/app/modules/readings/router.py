# ROUTER — readings
# Thin HTTP layer: validates schemas → calls the service → answers.
"""
Reading endpoints.

`POST /api/readings` (issue #24) is the endpoint the simulator uses and
the first link of the mandatory vertical flow (section 8.5 of the
document):

    Simulator → POST /api/readings → FastAPI → Service → Repository → PostgreSQL

**This router has no `prefix`.** It is the exception among the eight, on
purpose: it exposes routes that hang from different trees.

    POST /api/readings                              → issue #24
    GET  /api/sensors/{sensor_id}/readings          → issue #25 (history)
    GET  /api/sensors/{sensor_id}/readings/series   → B7 (chart)

They are all "readings" and share service and schemas, so they live in
the same module; but the last two are read from a sensor. With
`prefix="/readings"` the history would end up at
`/api/readings/sensors/{id}/readings`, which is not what the document
sets.

Note what is NOT in this file: no query, no rule, no `try/except`. The
router declares the route, FastAPI validates the body against the schema,
and it delegates. It is the acceptance criterion of issue #22: "No data
access logic inside the routers".
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.readings.schemas import (
    ReadingCreate,
    ReadingResponse,
    ReadingSeriesResponse,
    SeriesBucket,
)
from app.modules.readings.service import ReadingService, get_reading_service
from app.shared.dependencies import OrgScope, Pagination, require_ingest_key
from app.shared.schemas import Page, error_response

router = APIRouter(tags=["Readings"])

# The service is requested with Depends instead of being built in each
# endpoint. That way a test can replace it entirely without touching the
# router.
ReadingSvc = Annotated[ReadingService, Depends(get_reading_service)]


@router.post(
    "/readings",
    response_model=ReadingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store a reading",
    description=(
        "Receives a pressure measurement from a sensor. Used by the "
        "simulator (issue #16). Returns **201** with the stored reading.\n\n"
        "**Requires the `X-Ingest-Key` header** with the simulator key "
        "(`INGEST_API_KEY` in .env, issue #106). No session is needed: "
        "readings are sent by the simulator, not by a person.\n\n"
        "`measured_at` is optional: if not sent, the server uses the time "
        "it was received.\n\n"
        "If the pressure goes outside the sensor thresholds, a "
        "`LOW_PRESSURE` or `HIGH_PRESSURE` alert is opened (visible in "
        "`GET /api/alerts`). While it stays open, the next readings do not "
        "create another one; they can only raise it from `WARNING` to "
        "`CRITICAL`.\n\n"
        "`id` is optional. If a reading is resent with an `id` already "
        "stored and the same data, the existing one is returned without "
        "duplicating it or opening another alert."
    ),
    dependencies=[Depends(require_ingest_key)],
    responses={
        **error_response(
            status.HTTP_401_UNAUTHORIZED,
            "`X-Ingest-Key` is missing or is not the simulator key "
            "(`UNAUTHORIZED`).",
        ),
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "The given sensor does not exist (`SENSOR_NOT_FOUND`).",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "A reading with that `id` and different data already exists "
            "(`READING_ID_CONFLICT`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Pressure outside the 0–25 bar range, unknown field or "
            "malformed body.",
        ),
    },
)
def create_reading(payload: ReadingCreate, service: ReadingSvc) -> ReadingResponse:
    # `payload` arrives already validated: if the JSON did not fit
    # ReadingCreate, FastAPI stopped earlier and the validation handler
    # returned the 422.
    return service.create(payload)


@router.get(
    "/sensors/{sensor_id}/readings",
    response_model=Page[ReadingResponse],
    summary="Reading history of a sensor",
    description=(
        "Returns the readings of a sensor, paginated and ordered by "
        "measurement date: **newest first** by default, or the other way "
        "round with `?order=asc` (B7). `?from=&to=` limits it to that "
        "period, `to` excluded; a date without a time zone is taken as UTC "
        "and `from` after `to` gives 422 (`INVALID_DATE_RANGE`). Used by "
        "the sensor detail view (issue #40).\n\n"
        "It only returns sensors of **your own organization**: another "
        "client's `sensor_id` answers 404, like one that does not exist. "
        "Answering the same is deliberate — telling them apart would say "
        "whether that id exists somewhere."
    ),
    responses={
        **error_response(
            status.HTTP_401_UNAUTHORIZED,
            "No session (`UNAUTHORIZED`).",
        ),
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "Client account without an organization (`FORBIDDEN`).",
        ),
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "The sensor does not exist or is not from your organization "
            "(`SENSOR_NOT_FOUND`).",
        ),
    },
)
def list_sensor_readings(
    sensor_id: UUID,
    service: ReadingSvc,
    scope: OrgScope,
    pagination: Pagination,
    start: Annotated[
        datetime | None,
        Query(alias="from", description="From (ISO 8601, included)."),
    ] = None,
    end: Annotated[
        datetime | None,
        Query(alias="to", description="Until (ISO 8601, excluded)."),
    ] = None,
    order: Annotated[
        Literal["asc", "desc"],
        Query(description="`desc`: newest first."),
    ] = "desc",
) -> Page[ReadingResponse]:
    # The organization comes from the session (`OrgScope`), never from
    # what the client sends: if it came in the query, anyone could ask for
    # someone else's.
    return service.list_by_sensor(
        sensor_id=sensor_id,
        organization_id=scope,
        offset=pagination.offset,
        limit=pagination.limit,
        start=start,
        end=end,
        newest_first=order == "desc",
    )


@router.get(
    "/sensors/{sensor_id}/readings/series",
    response_model=ReadingSeriesResponse,
    summary="Pressure series of a sensor for the chart",
    description=(
        "Pressure of the last `days` days grouped in `bucket` slots (B7): "
        "each point brings the slot start (`t`) and the average, minimum "
        "and maximum pressure. Slots without readings are left out. It "
        "includes the sensor `min_pressure` and `max_pressure` to draw the "
        "allowed band.\n\n"
        "Same scope as the history: a sensor from another organization "
        "answers 404. More than 1000 points (for example, 30 days at "
        "15 min) gives 422 (`TOO_MANY_POINTS`)."
    ),
    responses={
        **error_response(
            status.HTTP_401_UNAUTHORIZED,
            "No session (`UNAUTHORIZED`).",
        ),
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "The sensor does not exist or is not from your organization "
            "(`SENSOR_NOT_FOUND`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Too many points (`TOO_MANY_POINTS`) or invalid parameters.",
        ),
    },
)
def sensor_readings_series(
    sensor_id: UUID,
    service: ReadingSvc,
    scope: OrgScope,
    days: Annotated[int, Query(ge=1, le=30, description="Days until now.")] = 7,
    bucket: Annotated[
        SeriesBucket, Query(description="Size of each slot.")
    ] = SeriesBucket.H2,
) -> ReadingSeriesResponse:
    return service.series(
        sensor_id=sensor_id, organization_id=scope, days=days, bucket=bucket
    )
