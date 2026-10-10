# ROUTER — analytics
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Endpoints de analítica (`/api/analytics/...`).

Registrado desde la issue #22. Los KPIs y agregaciones son nivel
Intermedio (apartado 9.2):

    GET /api/analytics/overview?from=&to=        B9 (Ana), pendiente
    GET /api/analytics/alerts/weekly?from=&to=   B9 (Ana), pendiente
    GET /api/analytics/export?format=csv&from=&to=   B18, implementado

El periodo de los tres sale de la dependencia compartida `DateRange`
(shared/dependencies.py): últimos 30 días por defecto y 422 si `from >= to`.
Cuando se implemente B9, `overview` y `weekly` solo tienen que recibir
`rango: DateRange` y filtrar por `rango.start` / `rango.end`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status

from app.modules.analytics.schemas import EXPORT_COLUMNS, ExportFormat
from app.modules.analytics.service import AnalyticsService, get_analytics_service
from app.shared.dependencies import DateRange, OrgScope
from app.shared.schemas import error_response

router = APIRouter(prefix="/analytics", tags=["Analytics"])

AnalyticsSvc = Annotated[AnalyticsService, Depends(get_analytics_service)]


@router.get(
    "/export",
    summary="Exportar la analítica del periodo",
    description=(
        "CSV con una fila por sensor y día: lecturas agregadas (número, "
        "mínimo, media y máximo) y alertas creadas ese día. Solo los datos "
        "de tu organización; un admin exporta todas.\n\n"
        "Periodo: `from` incluido, `to` excluido; por defecto, los últimos "
        "30 días. Máximo 366 días.\n\n"
        f"Columnas: `{'`, `'.join(EXPORT_COLUMNS)}`."
    ),
    response_class=Response,
    responses={
        200: {"content": {"text/csv": {}}, "description": "El archivo CSV."},
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
        Query(alias="format", description="Formato del archivo. Solo `csv`."),
    ] = ExportFormat.CSV,
) -> Response:
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
