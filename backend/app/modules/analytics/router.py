# ROUTER — analytics
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de analítica (`/api/analytics/...`).

Registrado desde la issue #22. Las rutas B9 agregan KPIs y rankings; B18
mantiene la exportación con rango de fechas:

    GET /api/analytics/overview              → B9 (#144, Ana)
    GET /api/analytics/alerts/weekly         → B9 (#144, Ana)
    GET /api/analytics/alerts/top-sensors    → B9 (#144, Ana)
    rango de fechas y exportación CSV        → B18 (#134, Daruny)

Se usa `overview`, como dice el documento (apartado 9.2), y no `kpis`,
como dibuja el diagrama de arquitectura.
`overview` usa los últimos 30 días para la mediana; `weekly` usa una semana
ISO explícita y `top-sensors` recibe `days`.
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


@router.get("/overview", response_model=OverviewResponse, summary="KPIs del panel")
def overview(service: AnalyticsSvc, user: CurrentUser, scope: OrgScope) -> OverviewResponse:
    return OverviewResponse.model_validate(service.overview(scope, user.role == "admin"))


@router.get("/alerts/weekly", response_model=WeeklyAlertsResponse, summary="Alertas por semana")
def weekly_alerts(
    service: AnalyticsSvc,
    scope: OrgScope,
    site_id: UUID,
    week_start: date | None = Query(default=None),
) -> WeeklyAlertsResponse:
    return WeeklyAlertsResponse.model_validate(service.weekly_alerts(site_id, week_start, scope))


@router.get("/alerts/top-sensors", response_model=TopSensorsResponse, summary="Sensores con más alertas")
def top_sensors(
    service: AnalyticsSvc,
    scope: OrgScope,
    days: Annotated[int, Query(ge=1, le=366)] = 30,
) -> TopSensorsResponse:
    return TopSensorsResponse.model_validate(service.top_sensors(days, scope))


@router.get(
    "/export",
    summary="Exportar la analítica del periodo",
    description=(
        "CSV con una fila por sensor y día: lecturas agregadas (número, "
        "mínimo, media y máximo) y alertas creadas ese día. Solo los datos "
        "de tu organización; un admin exporta todas.\n\n"
        "Periodo: `from` incluido, `to` excluido; por defecto, los últimos "
        "30 días. Máximo 366 días.\n\n"
        f"Columnas: `{'`, `'.join(EXPORT_COLUMNS)}`.\n\n"
        "Con `format=json` devuelve las mismas filas como lista JSON "
        "(presiones como número o `null`), sin descarga: es lo que usa el "
        "panel de analítica para los gráficos."
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
            "description": "El archivo CSV, o las filas en JSON con `format=json`.",
        },
        **error_response(status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."),
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "Cuenta de cliente sin organización (`FORBIDDEN`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Fechas o formato no válidos (`INVALID_DATE_RANGE`, `VALIDATION_ERROR`).",
        ),
    },
)
def export(
    service: AnalyticsSvc,
    scope: OrgScope,
    rango: DateRange,
    formato: Annotated[
        ExportFormat,
        Query(alias="format", description="`csv` (descarga) o `json` (para el panel)."),
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
