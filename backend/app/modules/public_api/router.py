"""Endpoints read-only para integraciones externas (subject Web major)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.alerts.schemas import AlertResponse, AlertSeverity, AlertState, AlertStatus
from app.modules.alerts.service import AlertService, get_alert_service
from app.modules.analytics.schemas import DailyRow, OverviewResponse
from app.modules.analytics.service import AnalyticsService, get_analytics_service
from app.modules.sensors.schemas import SensorResponse
from app.modules.sensors.service import SensorService, get_sensor_service
from app.modules.sites.schemas import SiteResponse
from app.modules.sites.service import SiteService, get_site_service
from app.shared.dependencies import DateRange, Pagination, Search
from app.shared.enums import SensorHealth
from app.shared.schemas import Page, error_response

from .auth import PublicOrganizationId

router = APIRouter(prefix="/public/v1", tags=["Public API"])

AnalyticsSvc = Annotated[AnalyticsService, Depends(get_analytics_service)]
SiteSvc = Annotated[SiteService, Depends(get_site_service)]
SensorSvc = Annotated[SensorService, Depends(get_sensor_service)]
AlertSvc = Annotated[AlertService, Depends(get_alert_service)]

_PUBLIC_ERRORS = {
    **error_response(
        status.HTTP_401_UNAUTHORIZED,
        "Falta la cabecera X-API-Key o la clave no es válida (`UNAUTHORIZED`).",
    ),
    **error_response(
        status.HTTP_400_BAD_REQUEST,
        "La API pública no está configurada correctamente (`PUBLIC_API_NOT_CONFIGURED`).",
    ),
    **error_response(
        status.HTTP_429_TOO_MANY_REQUESTS,
        "El límite de peticiones del gateway se ha superado (`TOO_MANY_REQUESTS`).",
    ),
}


@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Resumen de la organización",
    description=(
        "KPIs read-only de la organización asociada a la API key. No requiere "
        "cookie de sesión y nunca amplía el scope configurado."
    ),
    responses=_PUBLIC_ERRORS,
)
def public_overview(
    service: AnalyticsSvc, organization_id: PublicOrganizationId
) -> OverviewResponse:
    return OverviewResponse.model_validate(service.overview(organization_id, False))


@router.get(
    "/sites",
    response_model=Page[SiteResponse],
    summary="Listar edificios",
    description="Lista paginada de edificios de la organización asociada a la API key.",
    responses=_PUBLIC_ERRORS,
)
def public_sites(
    service: SiteSvc,
    organization_id: PublicOrganizationId,
    pagination: Pagination,
    q: Search,
) -> Page[SiteResponse]:
    return service.list(
        organization_id=organization_id,
        offset=pagination.offset,
        limit=pagination.limit,
        q=q,
    )


@router.get(
    "/sensors",
    response_model=Page[SensorResponse],
    summary="Listar sensores",
    description=(
        "Lista paginada de sensores, con salud y última lectura, limitada a "
        "la organización de la API key."
    ),
    responses=_PUBLIC_ERRORS,
)
def public_sensors(
    service: SensorSvc,
    organization_id: PublicOrganizationId,
    pagination: Pagination,
    q: Search,
    site_id: UUID | None = Query(default=None),
    health: SensorHealth | None = Query(default=None),
) -> Page[SensorResponse]:
    return service.list(
        organization_id=organization_id,
        offset=pagination.offset,
        limit=pagination.limit,
        q=q,
        site_id=site_id,
        health=health,
    )


@router.get(
    "/alerts",
    response_model=Page[AlertResponse],
    summary="Listar alertas",
    description=(
        "Lista paginada de alertas de la organización asociada a la API key. "
        "La API pública no expone acciones de reconocimiento ni resolución."
    ),
    responses=_PUBLIC_ERRORS,
)
def public_alerts(
    service: AlertSvc,
    organization_id: PublicOrganizationId,
    pagination: Pagination,
    q: Search,
    status_filter: Annotated[
        AlertStatus | None,
        Query(alias="status", description="ACTIVE o RESOLVED."),
    ] = None,
    severity: AlertSeverity | None = Query(default=None),
    state: AlertState | None = Query(default=None),
    site_id: UUID | None = Query(default=None),
) -> Page[AlertResponse]:
    return service.list(
        organization_id=organization_id,
        offset=pagination.offset,
        limit=pagination.limit,
        status=status_filter.value if status_filter else None,
        q=q,
        severity=severity.value if severity else None,
        state=state.value if state else None,
        site_id=site_id,
    )


@router.get(
    "/analytics/export",
    response_model=list[DailyRow],
    summary="Exportar analítica en JSON",
    description=(
        "Devuelve una fila por sensor y día con lecturas y alertas. El rango "
        "máximo es de 366 días y solo incluye la organización de la API key."
    ),
    responses=_PUBLIC_ERRORS,
)
def public_analytics_export(
    service: AnalyticsSvc,
    organization_id: PublicOrganizationId,
    rango: DateRange,
) -> list[DailyRow]:
    rows = service.export_rows(organization_id, rango.start, rango.end)
    return [DailyRow.model_validate(row) for row in rows]
