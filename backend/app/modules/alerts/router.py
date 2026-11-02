# ROUTER — alerts
# Thin HTTP layer: validates schemas → calls the service → answers.
# AlertService: rules, acknowledge, resolve (transactions).
"""
Alert endpoints (`/api/alerts/...`).

Implemented in issue #28 (PR #78); common filters of B0 (#138):

    GET   /api/alerts
    PATCH /api/alerts/{id}/acknowledge
    PATCH /api/alerts/{id}/resolve

Two design decisions:

**PATCH and not POST.** It is what section 9.1 of the document sets. (The
architecture diagram draws `POST .../resolve` and leaves out
`acknowledge`; the document, the team agreement, wins.) PATCH because the
whole alert is not replaced, only part of its state.

**Two routes and not one `PATCH /api/alerts/{id}` with a `status`
field.** Acknowledging and resolving are not two ways of writing the same
thing: they are different actions, with different effects and
permissions, and splitting them lets them be authorized separately (only
an admin resolves).

There will be no `POST /api/alerts`: the backend creates alerts when it
processes readings, never the client (section 1.3).
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.alerts.schemas import AlertResponse, AlertSeverity, AlertState, AlertStatus
from app.modules.alerts.service import AlertService, get_alert_service
from app.shared.dependencies import (
    CurrentUser,
    OrganizationIdFilter,
    OrgScope,
    Pagination,
    Search,
    SensorIdFilter,
    SiteIdFilter,
    require_role,
    require_trial_not_expired,
)
from app.shared.schemas import Page, error_response

router = APIRouter(prefix="/alerts", tags=["Alerts"])

AlertSvc = Annotated[AlertService, Depends(get_alert_service)]

_NO_AUTORIZADO = {
    **error_response(
        status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."
    ),
    **error_response(
        status.HTTP_403_FORBIDDEN,
        "Client account without an organization (`FORBIDDEN`).",
    ),
}
_NO_ENCONTRADA = error_response(
    status.HTTP_404_NOT_FOUND,
    "The alert does not exist, or is not from your organization (`ALERT_NOT_FOUND`).",
)
# Client writes: with the trial over, read-only (B12).
_SOLO_LECTURA_SI_CADUCA = [Depends(require_trial_not_expired)]
_NO_PUEDE_ESCRIBIR = {
    **_NO_AUTORIZADO,
    **error_response(
        status.HTTP_403_FORBIDDEN,
        "Client account without an organization (`FORBIDDEN`), or the trial "
        "is over and the account is read-only (`TRIAL_EXPIRED`).",
    ),
}


@router.get(
    "",
    response_model=Page[AlertResponse],
    summary="List alerts",
    description=(
        "Alerts of your organization, paginated. An admin sees those of "
        "every organization.\n\n"
        "`status` shows only the active ones, the default view of whoever "
        "handles them, and `sensor_id` is used to come in from a sensor "
        "detail.\n\n"
        "Common filters: `q` searches the message, the sensor name and code, the building and the client; "
        "`organization_id` and `site_id` keep only those of one client or "
        "one building. All filters are combined with AND. `severity` "
        "filters the severity and `state` the derived state (ACTIVE "
        "unacknowledged, ACKNOWLEDGED active and acknowledged, RESOLVED "
        "closed). `status=ACTIVE` also includes the acknowledged ones. "
        "Incompatible combinations give an empty list. `created_from` "
        "included and `created_to` excluded limit the creation date; "
        "without dates the whole history is shown. Dates without a zone "
        "are read as UTC."
    ),
    responses={
        **_NO_AUTORIZADO,
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Invalid filters (`VALIDATION_ERROR`) or created_from >= "
            "created_to (`INVALID_DATE_RANGE`).",
        ),
    },
)
def list_alerts(
    service: AlertSvc,
    scope: OrgScope,
    pagination: Pagination,
    q: Search,
    status_filtro: Annotated[
        AlertStatus | None,
        Query(alias="status", description="Keeps only the alerts in that status."),
    ] = None,
    sensor_id: SensorIdFilter = None,
    organization_id: OrganizationIdFilter = None,
    site_id: SiteIdFilter = None,
    severity: Annotated[AlertSeverity | None, Query(description="Alert severity.")] = None,
    state: Annotated[AlertState | None, Query(description="Derived state for the screens.")] = None,
    created_from: Annotated[
        datetime | None,
        Query(description="Created from (ISO 8601, included). Without a zone: UTC."),
    ] = None,
    created_to: Annotated[
        datetime | None,
        Query(description="Created until (ISO 8601, excluded). Without a zone: UTC."),
    ] = None,
) -> Page[AlertResponse]:
    # The organization comes from the session (`OrgScope`), never from the
    # query: if it came from outside, anyone could ask for another client's
    # alerts.
    return service.list(
        organization_id=scope,
        offset=pagination.offset,
        limit=pagination.limit,
        status=status_filtro.value if status_filtro else None,
        sensor_id=sensor_id,
        q=q,
        organization_filter=organization_id,
        site_id=site_id,
        severity=severity.value if severity else None,
        state=state.value if state else None,
        created_from=created_from,
        created_to=created_to,
    )


@router.patch(
    "/{alert_id}/acknowledge",
    response_model=AlertResponse,
    summary="Mark an alert as seen",
    description=(
        "Records that someone is aware of the alert.\n\n"
        "**It does not close it:** the alert stays active. And it is "
        "idempotent — if two operators press at the same time, the second "
        "call neither fails nor overwrites the time or the user of the "
        "first. The session user is recorded. A resolved alert can be "
        "acknowledged: it stays RESOLVED."
    ),
    dependencies=_SOLO_LECTURA_SI_CADUCA,
    responses={**_NO_PUEDE_ESCRIBIR, **_NO_ENCONTRADA},
)
def acknowledge_alert(
    alert_id: UUID, service: AlertSvc, scope: OrgScope, user: CurrentUser
) -> AlertResponse:
    return service.acknowledge(alert_id, organization_id=scope, actor_id=user.id)


@router.patch(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Close an alert (AquaGuard only)",
    description=(
        "Marks the alert as handled. **Admin only**: the client says \"Me "
        "encargo\" (`acknowledge`), but AquaGuard confirms the water is "
        "fine again. A client gets 403. Alerts also close on their own "
        "after 15 minutes of normal readings (#277).\n\n"
        "Resolving one already resolved answers **409**, not a silent "
        "success: it would overwrite the closing date and lose when it was "
        "really handled. The session user is recorded; no previous "
        "acknowledgement is required and the existing one is not changed."
    ),
    dependencies=[Depends(require_role("admin"))],
    responses={
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "The session is not an admin one (`FORBIDDEN`): the client does not close alerts.",
        ),
        **_NO_ENCONTRADA,
        **error_response(
            status.HTTP_409_CONFLICT,
            "The alert was already resolved (`ALERT_ALREADY_RESOLVED`).",
        ),
    },
)
def resolve_alert(
    alert_id: UUID, service: AlertSvc, scope: OrgScope, user: CurrentUser
) -> AlertResponse:
    return service.resolve(alert_id, organization_id=scope, actor_id=user.id)
