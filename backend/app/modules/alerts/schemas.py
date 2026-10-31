# SCHEMAS — alerts
# Pydantic request/response (OpenAPI contract). Never return a raw ORM model.
"""
Alerts contract (issue #23).

Fields according to the domain model of the document (section 5):

    alerts: id, sensor_id, type, severity, message, status,
            created_at, resolved_at

    type     → LOW_PRESSURE | HIGH_PRESSURE | SENSOR_OFFLINE
    status   → ACTIVE | RESOLVED
    severity → WARNING | CRITICAL

Alerts are **created by the backend**, never by the client: the
document is explicit that the simulator only generates measurements and
that anomaly detection is business logic (section 1.3). That is why there
is no `AlertCreate` in this contract — there is no `POST /api/alerts`.
They are only listed and their state changed.

--------------------------------------------------------------------
"Acknowledge": stored state versus computed state
--------------------------------------------------------------------
Section 9.1 defines two different endpoints:

    PATCH /api/alerts/{id}/acknowledge
    PATCH /api/alerts/{id}/resolve

The table only stores `status` ACTIVE / RESOLVED, plus
`acknowledged_at` (decided with Daruny before the migration).
Acknowledging and resolving are independent facts, not stages of one
scale: with a three-value enum in the table, when an alert was
acknowledged would be lost as soon as someone resolves it.

The screens do want a single three-value state. That is why the response
brings `state` (`AlertState`, B0), computed from the two stored fields.
See `shared/enums.py`.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

# The enums live in shared/enums.py (B0); they are re-exported from here
# because the rules, the service and the tests already import them from
# this module.
from app.shared.enums import AlertSeverity, AlertState, AlertStatus, AlertType
from app.shared.schemas import ApiModel


class AlertNotificationResponse(ApiModel):
    """A notice sent to the client because nobody was handling it (#275)."""

    attempt: int = Field(description="1 = first notice, 2 = second…")
    channel: str = Field(description="How it was sent. Only EMAIL today.")
    recipient: str = Field(description="Who to: one or more emails separated by \", \".")
    sent_at: datetime = Field(description="When, in UTC.")


class AlertResponse(ApiModel):
    id: UUID
    sensor_id: UUID = Field(description="Sensor that raised the alert.")
    # Read-only fields (B0): to show "Hotel Sol · Planta 2 · Sensor bombas"
    # without asking for the sensor, the site and the organization
    # separately.
    sensor_name: str = Field(description="Sensor name.")
    site_id: UUID = Field(description="Building of the sensor.")
    site_name: str = Field(description="Building name.")
    organization_id: UUID = Field(description="Organization of the building.")
    organization_name: str = Field(description="Organization name.")
    floor: int = Field(
        description="Floor of the sensor. 0 is the ground floor; negative, a basement."
    )
    type: AlertType
    severity: AlertSeverity
    message: str = Field(
        description="Readable description of the problem.",
        examples=["Presión por debajo del umbral: 0.8 bar (mínimo 1.5)"],
    )
    threshold: float | None = Field(
        default=None,
        description=(
            "The sensor limit that was crossed, in bar: the minimum for "
            "LOW_PRESSURE and the maximum for HIGH_PRESSURE. Null for "
            "SENSOR_OFFLINE. It is the current sensor limit: if it changes "
            "later, the new one shows here."
        ),
        examples=[1.5],
    )
    status: AlertStatus = Field(
        description="Stored status: ACTIVE or RESOLVED. See also `state`."
    )
    state: AlertState = Field(
        description=(
            "State for the screens, computed: RESOLVED if resolved, "
            "ACKNOWLEDGED if still active but someone has acknowledged it, "
            "ACTIVE if nobody has acknowledged it."
        )
    )
    created_at: datetime = Field(description="When it was generated, in UTC.")
    acknowledged_at: datetime | None = Field(
        default=None,
        description=(
            "When the alert was acknowledged, in UTC. Null if nobody has "
            "acknowledged it yet."
        ),
    )
    resolved_at: datetime | None = Field(
        default=None,
        description="When it was resolved, in UTC. Null while still active.",
    )
    acknowledged_by_name: str | None = Field(
        default=None, description="Name of who acknowledged it; null if unknown or deleted."
    )
    resolved_by_name: str | None = Field(
        default=None, description="Name of who resolved it; null if unknown or deleted."
    )
    notifications: list[AlertNotificationResponse] = Field(
        default_factory=list,
        description=(
            "Notices sent to the client while the alert was still unhandled "
            "(#275), in order. Empty if none has been sent."
        ),
    )
    next_notification_at: datetime | None = Field(
        default=None,
        description=(
            "When the next email is due, in UTC. Null if none is due any more: "
            "all sent, someone is handling it or it is closed."
        ),
    )
    normal_since: datetime | None = Field(
        default=None,
        description=(
            "Since when the readings are normal again, in UTC, if the alert "
            "is still open (#277). Null if they are not or it is closed."
        ),
    )
    closes_at: datetime | None = Field(
        default=None,
        description=(
            "When it will close on its own if they stay normal: `normal_since` + 15 min. "
            "When closed, `resolved_at` will be `normal_since`."
        ),
    )
    resolution_minutes: float | None = Field(
        default=None,
        description="Minutes from creation to resolution, with decimals; null if still open or the closing date is missing.",
    )
