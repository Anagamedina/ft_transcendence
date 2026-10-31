"""Endpoints for external integrations (subject Web major).

The GETs work with either key; creating, replacing and deleting buildings
needs the write key (see `auth.py`).
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
        "The X-API-Key header is missing or the key is not valid (`UNAUTHORIZED`).",
    ),
    **error_response(
        status.HTTP_400_BAD_REQUEST,
        "The public API is not configured correctly (`PUBLIC_API_NOT_CONFIGURED`).",
    ),
    **error_response(
        status.HTTP_403_FORBIDDEN,
        "The organization is suspended (`ACCOUNT_DISABLED`).",
    ),
    **error_response(
        status.HTTP_429_TOO_MANY_REQUESTS,
        "The gateway rate limit was exceeded (`TOO_MANY_REQUESTS`).",
    ),
}
_WRITE_ERRORS = {
    **_PUBLIC_ERRORS,
    **error_response(
        status.HTTP_403_FORBIDDEN,
        "The API key is read-only (`PUBLIC_API_READ_ONLY`), the "
        "organization is suspended (`ACCOUNT_DISABLED`) or its trial is "
        "over (`TRIAL_EXPIRED`).",
    ),
}
_SITE_NOT_FOUND = error_response(
    status.HTTP_404_NOT_FOUND,
    "The building does not exist or belongs to another organization (`SITE_NOT_FOUND`).",
)


@router.get(
    "/overview",
    response_model=OverviewResponse,
    summary="Organization overview",
    description=(
        "KPIs of the organization tied to the API key. It needs no session "
        "cookie and never widens the configured scope."
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
    summary="List buildings",
    description="Paginated list of buildings of the organization tied to the API key.",
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
    summary="Get a building",
    description="A building of the API key organization.",
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
    summary="Create a building",
    description=(
        "Creates a building in the API key organization. Requires "
        "`PUBLIC_API_WRITE_KEY`. It respects the building limit of the "
        "contract or the trial (`SITE_LIMIT_REACHED`)."
    ),
    responses={
        **_WRITE_ERRORS,
        **error_response(
            status.HTTP_409_CONFLICT,
            "There is already a building with that name (`SITE_NAME_TAKEN`) or "
            "the building limit was reached (`SITE_LIMIT_REACHED`).",
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
    summary="Replace a building",
    description=(
        "Replaces all the editable data of a building of the API key "
        "organization: an optional field that is not sent goes back to its "
        "default. Requires `PUBLIC_API_WRITE_KEY`. Removing floors with "
        "sensors answers 422 `FLOOR_OUT_OF_SITE`."
    ),
    responses={
        **_WRITE_ERRORS,
        **_SITE_NOT_FOUND,
        **error_response(
            status.HTTP_409_CONFLICT,
            "There is already a building with that name (`SITE_NAME_TAKEN`).",
        ),
    },
)
def public_replace_site(
    site_id: UUID,
    payload: PublicSiteWrite,
    service: SiteSvc,
    organization_id: PublicWriteOrganizationId,
) -> SiteResponse:
    # The admin service does not look at the organization: before touching
    # anything it checks that the building belongs to the key's one (404 if
    # not).
    service.get(site_id, organization_id)
    return service.update(site_id, SiteUpdate(**payload.model_dump()))


@router.delete(
    "/sites/{site_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a building",
    description=(
        "Deletes an empty building of the API key organization. Requires "
        "`PUBLIC_API_WRITE_KEY`. With sensors or documents it answers 409."
    ),
    responses={
        **_WRITE_ERRORS,
        **_SITE_NOT_FOUND,
        **error_response(
            status.HTTP_409_CONFLICT,
            "The building has sensors (`SITE_HAS_SENSORS`) or documents "
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
    summary="List sensors",
    description=(
        "Paginated list of sensors, with health and last reading, limited to "
        "the API key organization."
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
    summary="List alerts",
    description=(
        "Paginated list of alerts of the organization tied to the API key. "
        "The public API exposes no acknowledge or resolve actions."
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
        Query(alias="status", description="ACTIVE or RESOLVED."),
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
    summary="Export analytics in JSON",
    description=(
        "Returns one row per sensor and day with readings and alerts. The "
        "maximum range is 366 days and it only includes the API key "
        "organization."
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
