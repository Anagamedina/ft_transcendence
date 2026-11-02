# ROUTER — analytics
# Thin HTTP layer: validates schemas → calls the service → answers.
"""
Analytics endpoints (`/api/analytics/...`).

Registered since issue #22. The B9 routes aggregate KPIs and rankings; B18
keeps the export with a date range:

    GET /api/analytics/overview              → B9 (#144, Ana)
    GET /api/analytics/alerts/weekly         → B9 (#144, Ana)
    GET /api/analytics/alerts/top-sensors    → B9 (#144, Ana)
    date range and CSV export               → B18 (#134, Daruny)

It is called `overview`, as the document says (section 9.2), and not
`kpis`, as the architecture diagram draws.
`overview` uses the last 30 days for the median; `weekly` uses an explicit
ISO week and `top-sensors` gets `days`.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from app.modules.analytics.schemas import (
    EXPORT_COLUMNS,
    DailyRow,
    ExportFormat,
    OverviewResponse,
    TopSensorsResponse,
    WeeklyAlertsResponse,
)
from app.modules.analytics.service import AnalyticsService, get_analytics_service
from app.shared.dependencies import CurrentUser, DateRange, OrgScope
from app.shared.schemas import error_response

router = APIRouter(prefix="/analytics", tags=["Analytics"])

AnalyticsSvc = Annotated[AnalyticsService, Depends(get_analytics_service)]


@router.get("/overview", response_model=OverviewResponse, summary="Panel KPIs")
def overview(service: AnalyticsSvc, user: CurrentUser, scope: OrgScope) -> OverviewResponse:
    return OverviewResponse.model_validate(service.overview(scope, user.role == "admin"))


@router.get("/alerts/weekly", response_model=WeeklyAlertsResponse, summary="Alerts per week")
def weekly_alerts(
    service: AnalyticsSvc,
    scope: OrgScope,
    site_id: UUID,
    week_start: date | None = Query(default=None),
) -> WeeklyAlertsResponse:
    return WeeklyAlertsResponse.model_validate(service.weekly_alerts(site_id, week_start, scope))


@router.get("/alerts/top-sensors", response_model=TopSensorsResponse, summary="Sensors with the most alerts")
def top_sensors(
    service: AnalyticsSvc,
    scope: OrgScope,
    days: Annotated[int, Query(ge=1, le=366)] = 30,
) -> TopSensorsResponse:
    return TopSensorsResponse.model_validate(service.top_sensors(days, scope))


@router.get(
    "/export",
    summary="Export the analytics of the period",
    description=(
        "CSV with one row per sensor and day: aggregated readings (count, "
        "minimum, average and maximum) and alerts created that day. Only "
        "the data of your organization; an admin exports all of them.\n\n"
        "Period: `from` included, `to` excluded; by default, the last 30 "
        "days. At most 366 days.\n\n"
        f"Columns: `{'`, `'.join(EXPORT_COLUMNS)}`.\n\n"
        "With `format=json` it returns the same rows as a JSON list "
        "(pressures as a number or `null`), without a download: it is what "
        "the analytics panel uses for the charts."
    ),
    response_class=Response,
    responses={
        200: {
            "content": {
                "text/csv": {},
                "application/json": {
                    "schema": {"type": "array", "items": DailyRow.model_json_schema()}
                },
            },
            "description": "The CSV file, or the rows in JSON with `format=json`.",
        },
        **error_response(status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."),
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "Client account without an organization (`FORBIDDEN`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Invalid dates or format (`INVALID_DATE_RANGE`, `VALIDATION_ERROR`).",
        ),
    },
)
def export(
    service: AnalyticsSvc,
    scope: OrgScope,
    rango: DateRange,
    formato: Annotated[
        ExportFormat,
        Query(alias="format", description="`csv` (download) or `json` (for the panel)."),
    ] = ExportFormat.CSV,
) -> Response:
    if formato is ExportFormat.JSON:
        filas = service.export_rows(scope, rango.start, rango.end)
        return JSONResponse(
            jsonable_encoder([DailyRow.model_validate(f) for f in filas])
        )

    contenido = service.export_csv(scope, rango.start, rango.end)
    nombre = (
        f"aquaguard-analytics_{rango.start:%Y-%m-%d}_{rango.end:%Y-%m-%d}.csv"
    )
    return Response(
        content=contenido,
        media_type="text/csv; charset=utf-8",
        # attachment: the browser downloads it instead of showing it.
        headers={"Content-Disposition": f'attachment; filename="{nombre}"'},
    )
