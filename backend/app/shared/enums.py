# ENUMS — shared vocabulary of the API (issue #138, B0).
# One single place for the values several modules share.
"""
Closed values of the API (issue #138, B0).

Before B0 each module declared its own. With the redesign, the same words
appear on several screens and in several endpoints: the status of an
organization shows up in the client list, on its page and in My account.
If each module writes it on its own, sooner or later one says `TRIAL` and
another `TRIALING`. That is why they all live here.

Convention: values in `UPPER_SNAKE_CASE`, equal to the name. Modules
import them from here and do not redefine them; they can still be
imported from `modules/*/schemas.py`, which re-export them.

The only exception is `UserRole` (`admin` / `client`, lowercase), which
stays in `users/schemas.py`: that is how it is stored in the table and how
the frontend and the cookie already use it. Changing it adds nothing and
breaks everyone.

**Stored** states versus **computed** states:

- Stored (the table has a CHECK with the same values):
  `OrganizationStatus`, `SubscriptionPlan`, `BuildingType`, `SensorType`,
  `DocumentKind`, `AlertType`, `AlertSeverity`, `AlertStatus`. Changing
  one means changing its CHECK with a migration (Daruny).
- Computed when answering, never stored: `SiteStatus`, `SensorStatus`,
  `SensorHealth`, `AlertState`, `InvitationStatus`.
"""

from __future__ import annotations

from enum import Enum


# ---------------------------------------------------------
# ORGANIZATIONS
# ---------------------------------------------------------
class OrganizationStatus(str, Enum):
    """
    Commercial situation of the client. CHECK `ck_organizations_status`.

    - `TRIAL`     → 7-day trial of the public sign-up (B10).
    - `ACTIVE`    → paying client. Older organizations are this.
    - `SUSPENDED` → its users cannot log in (B1).
    """

    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"


class SubscriptionPlan(str, Enum):
    """
    Plan chosen when going from trial to client (B14). CHECK
    `ck_organizations_plan`. The catalog with prices and limits is in
    `modules/subscriptions/plans.py`.
    """

    BASIC = "BASIC"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class BillingPeriod(str, Enum):
    """
    How often the plan is charged (B14). CHECK `ck_organizations_billing_period`.

    - `MONTHLY` → the plan price every month, no commitment.
    - `YEARLY`  → ten months in advance: two months free.
    """

    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


# ---------------------------------------------------------
# BUILDINGS
# ---------------------------------------------------------
class BuildingType(str, Enum):
    """Building type. CHECK `ck_sites_building_type`. B2."""

    HOTEL = "HOTEL"
    COMMUNITY = "COMMUNITY"
    OFFICE = "OFFICE"
    SPORTS = "SPORTS"
    RESIDENCE = "RESIDENCE"
    INDUSTRIAL = "INDUSTRIAL"
    OTHER = "OTHER"


class SiteStatus(str, Enum):
    """
    Status of a building, computed from its open alerts (B2).

    - `CRITICAL` → some sensor has an unresolved CRITICAL alert.
    - `WARNING`  → it only has unresolved WARNING alerts.
    - `OK`       → no open alert.

    Decided by Ana on 2026-10-10. It is the same rule the map uses to
    color its markers. A disconnected sensor already opens a CRITICAL
    `SENSOR_OFFLINE` alert, so it counts too.
    """

    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


# ---------------------------------------------------------
# SENSORS
# ---------------------------------------------------------
class SensorType(str, Enum):
    """
    Quantity the sensor measures.

    The document sets pressure as the main measurement and flow as
    optional (section 1.2). The MVP and the simulator work with PRESSURE;
    FLOW is declared so the contract does not have to change later.
    """

    PRESSURE = "PRESSURE"
    FLOW = "FLOW"


class SensorStatus(str, Enum):
    """
    Operational status of the sensor: is it sending readings?

    - `ONLINE`   → it has sent readings within the expected window.
    - `OFFLINE`  → it has gone too long without sending (issue #28).

    The backend computes it from `last_seen_at` (`sensors/status.py`); the
    client cannot write it.
    """

    ONLINE = "ONLINE"
    OFFLINE = "OFFLINE"


class SensorHealth(str, Enum):
    """
    Health of the sensor as the screens paint it: the color of the dot on
    the building floor. Computed, never stored.

    It joins the two questions that matter to whoever looks at the panel:
    is it sending data? and is what it sends fine? In order of priority:

    - `OFFLINE`  → more than 5 minutes without readings (same rule as
      `SensorStatus`, in `sensors/status.py`).
    - `CRITICAL` → it has an active alert of CRITICAL severity.
    - `WARNING`  → it has an active alert of WARNING severity.
    - `OK`       → everything else.

    It does not replace `SensorStatus`: the frontend already uses `status`
    and it stays. The computation and the `health` field in the response
    come from B3.
    """

    OK = "OK"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    OFFLINE = "OFFLINE"


# ---------------------------------------------------------
# DOCUMENTS
# ---------------------------------------------------------
class DocumentKind(str, Enum):
    """Type of a building document. CHECK `ck_documents_kind`. B11."""

    PLAN = "PLAN"
    REPORT = "REPORT"
    INVOICE = "INVOICE"
    PHOTO = "PHOTO"
    OTHER = "OTHER"


# ---------------------------------------------------------
# ALERTS
# ---------------------------------------------------------
class AlertType(str, Enum):
    """Rule that fired the alert. The three cases of section 1.2."""

    LOW_PRESSURE = "LOW_PRESSURE"
    HIGH_PRESSURE = "HIGH_PRESSURE"
    SENSOR_OFFLINE = "SENSOR_OFFLINE"


class AlertSeverity(str, Enum):
    """
    Severity.

    It is different from the type: low pressure can be WARNING if it
    grazes the threshold and CRITICAL if it collapses (issue #28).
    """

    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """
    Life cycle **stored** in the table. CHECK `ck_alerts_status`.

    Only two values: acknowledging an alert does not change its `status`,
    it fills `acknowledged_at`. What the screen shows is `AlertState`.
    """

    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


class AlertState(str, Enum):
    """
    State of the alert as the screens show it. Computed.

    - `RESOLVED`     → `status` is RESOLVED.
    - `ACKNOWLEDGED` → still active, but someone has acknowledged it.
    - `ACTIVE`       → still active and nobody has acknowledged it.

    It is derived from `status` + `acknowledged_at` instead of adding a
    third value to the table: the CHECK stays untouched and we do not lose
    when an alert that was later resolved had been acknowledged.
    """

    ACTIVE = "ACTIVE"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"

    @classmethod
    def derive(cls, status: str, acknowledged_at: object | None) -> "AlertState":
        """`status` is the table one; `acknowledged_at`, its column."""
        if status == AlertStatus.RESOLVED.value:
            return cls.RESOLVED
        if acknowledged_at is not None:
            return cls.ACKNOWLEDGED
        return cls.ACTIVE


# ---------------------------------------------------------
# INVITATIONS — B4 contract (#141)
# ---------------------------------------------------------
class InvitationStatus(str, Enum):
    """
    Status of an invitation. Computed: the table (D3, Daruny) stores
    dates, not a status.

    - `ACCEPTED` → `accepted_at` has a date.
    - `REVOKED`  → `revoked_at` has a date.
    - `EXPIRED`  → neither accepted nor revoked, and `expires_at` has passed.
    - `PENDING`  → neither accepted nor revoked, and not expired yet.
    """

    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
