"""Endpoints para integraciones externas (subject Web major).

Los GET valen con cualquiera de las dos claves; crear, reemplazar y borrar
edificios necesita la de escritura (ver `auth.py`).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from app.modules.alerts.schemas import AlertResponse, AlertSeverity, AlertState, AlertStatus
from app.modules.alerts.service import AlertService, get_alert_service
from app.modules.analytics.schemas import DailyRow, OverviewResponse
from app.modules.analytics.service import AnalyticsService, get_analytics_service
from app.modules.sensors.schemas import SensorResponse
from app.modules.sensors.service import SensorService, get_sensor_service
from app.modules.sites.schemas import SiteCreate, SiteResponse, SiteUpdate
from app.modules.sites.service import SiteService, get_site_service
from app.shared.dependencies import DateRange, Pagination, Search
from app.shared.enums import SensorHealth
from app.shared.schemas import Page, error_response

from .auth import PublicOrganizationId, PublicWriteOrganizationId
from .schemas import PublicSiteWrite

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
        status.HTTP_403_FORBIDDEN,
        "La organización está suspendida (`ACCOUNT_DISABLED`).",
    ),
    **error_response(
        status.HTTP_429_TOO_MANY_REQUESTS,
        "El límite de peticiones del gateway se ha superado (`TOO_MANY_REQUESTS`).",
    ),
}
_WRITE_ERRORS = {
    **_PUBLIC_ERRORS,
    **error_response(
        status.HTTP_403_FORBIDDEN,
        "La API key es de solo lectura (`PUBLIC_API_READ_ONLY`), la "
        "organización está suspendida (`ACCOUNT_DISABLED`) o su prueba ha "
        "vencido (`TRIAL_EXPIRED`).",
    ),
}
_SITE_NOT_FOUND = error_response(
    status.HTTP_404_NOT_FOUND,
    "El edificio no existe o es de otra organización (`SITE_NOT_FOUND`).",
)


@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Resumen de la organización",
    description=(
        "KPIs de la organización asociada a la API key. No requiere "
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
    "/sites/{site_id}",
    response_model=SiteResponse,
    summary="Ver un edificio",
    description="Un edificio de la organización de la API key.",
    responses={**_PUBLIC_ERRORS, **_SITE_NOT_FOUND},
)
def public_site(
    site_id: UUID, service: SiteSvc, organization_id: PublicOrganizationId
) -> SiteResponse:
    return service.get(site_id, organization_id)


@router.post(
    "/sites",
    response_model=SiteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un edificio",
    description=(
        "Crea un edificio en la organización de la API key. Requiere "
        "`PUBLIC_API_WRITE_KEY`. Respeta el límite de edificios del contrato "
        "o de la prueba (`SITE_LIMIT_REACHED`)."
    ),
    responses={
        **_WRITE_ERRORS,
        **error_response(
            status.HTTP_409_CONFLICT,
            "Ya hay un edificio con ese nombre (`SITE_NAME_TAKEN`) o se ha "
            "llegado al límite de edificios (`SITE_LIMIT_REACHED`).",
        ),
    },
)
def public_create_site(
    payload: PublicSiteWrite,
    service: SiteSvc,
    organization_id: PublicWriteOrganizationId,
) -> SiteResponse:
    return service.create(
        SiteCreate(**payload.model_dump(), organization_id=organization_id)
    )


@router.put(
    "/sites/{site_id}",
    response_model=SiteResponse,
    summary="Reemplazar un edificio",
    description=(
        "Reemplaza todos los datos editables de un edificio de la "
        "organización de la API key: un campo opcional que no se envía vuelve "
        "a su valor por defecto. Requiere `PUBLIC_API_WRITE_KEY`. Quitar "
        "plantas con sensores responde 422 `FLOOR_OUT_OF_SITE`."
    ),
    responses={
        **_WRITE_ERRORS,
        **_SITE_NOT_FOUND,
        **error_response(
            status.HTTP_409_CONFLICT,
            "Ya hay un edificio con ese nombre (`SITE_NAME_TAKEN`).",
        ),
    },
)
def public_replace_site(
    site_id: UUID,
    payload: PublicSiteWrite,
    service: SiteSvc,
    organization_id: PublicWriteOrganizationId,
) -> SiteResponse:
    # El servicio del admin no mira la organización: antes de tocar nada se
    # comprueba que el edificio es de la de la clave (404 si no).
    service.get(site_id, organization_id)
    return service.update(site_id, SiteUpdate(**payload.model_dump()))


@router.delete(
    "/sites/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un edificio",
    description=(
        "Borra un edificio vacío de la organización de la API key. Requiere "
        "`PUBLIC_API_WRITE_KEY`. Con sensores o documentos responde 409."
    ),
    responses={
        **_WRITE_ERRORS,
        **_SITE_NOT_FOUND,
        **error_response(
            status.HTTP_409_CONFLICT,
            "El edificio tiene sensores (`SITE_HAS_SENSORS`) o documentos "
            "(`SITE_HAS_DOCUMENTS`).",
        ),
    },
)
def public_delete_site(
    site_id: UUID, service: SiteSvc, organization_id: PublicWriteOrganizationId
) -> Response:
    service.get(site_id, organization_id)
    service.delete(site_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


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
