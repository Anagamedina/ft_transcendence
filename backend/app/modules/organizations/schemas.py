# SCHEMAS — organizations
# Pydantic request/response (OpenAPI contract). Never return a raw ORM model.
"""
Organizations contract (issue #23).

The organization is the AquaGuard client: a community, a town council or
a company. It is also the **isolation unit** of the whole system.

    organization → sites → sensors → readings → alerts

Everything hangs from it, and that chain is what lets the question "can
this user see this reading?" be answered by going up the relationships to
the organization. `get_org_scope` (issue #27) enforces the isolation, and
the contract reflects it by exposing `organization_id` on the resources
that depend on it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import EmailStr, Field

from app.modules.sites.schemas import SiteBase
from app.shared.enums import BillingPeriod, OrganizationStatus, SubscriptionPlan
from app.shared.schemas import ApiModel, ApiRequest

# Organization names are stored with 120 characters at most (`name`
# column and migration of #120).
NAME_MAX = 120

# Columns the list can be sorted by: the same the Clients table shows,
# with the field name of `OrganizationResponse`.
OrganizationSort = Literal[
    "name", "trial_ends_at", "site_count", "sensor_count", "user_count", "open_alerts"
]


class OrganizationContact(ApiRequest):
    """
    Contact and billing data (B1, columns from D1).

    All optional except the phone on creation: the admin creates a client
    and fills in the rest over time. Only the type and length of each
    column are checked here; the service normalizes them with the shared
    rules of `app/shared/fields.py` (spaces, lowercase emails, Spanish
    phone, tax id without separators).
    """

    city: str | None = Field(default=None, max_length=120, examples=["Barcelona"])
    contact_email: EmailStr | None = Field(
        default=None, description="Contact email of the client."
    )
    phone: str | None = Field(default=None, max_length=30, examples=["+34 600 000 000"])
    legal_name: str | None = Field(
        default=None, max_length=200, description="Legal company name.",
        examples=["Hoteles Diagonal S.L."],
    )
    tax_id: str | None = Field(
        default=None, max_length=30, description="Tax id (NIF or CIF).", examples=["B12345678"]
    )
    billing_email: EmailStr | None = Field(
        default=None, description="Email the invoices are sent to."
    )
    billing_address: str | None = Field(
        default=None, max_length=200, description="Billing address.",
        examples=["Avinguda Diagonal 100, 08019"],
    )


class OrganizationCreate(OrganizationContact):
    """
    Creation of an organization (admin only). It starts on trial (`TRIAL`,
    expiring in `TRIAL_DAYS`), like the public sign-up one (B10): it
    becomes `ACTIVE` when the client subscribes from "Hazte cliente"
    (B14).

    An empty or spaces-only name is rejected by the service, not the
    schema, to answer with the `INVALID_NAME` code #121 asks for instead of
    the generic `VALIDATION_ERROR`.
    """

    name: str = Field(
        max_length=NAME_MAX,
        description=(
            "Organization name: letters, numbers, spaces and "
            "`. , ' ’ - & ( )`. It cannot be empty nor repeat (ignoring "
            "case)."
        ),
        examples=["Hotel Diagonal Mar"],
    )
    phone: str = Field(
        max_length=30,
        description=(
            "Spanish phone, mandatory. Stored as `+34 612 345 678`; if it is "
            "not valid, 422 `INVALID_PHONE`."
        ),
        examples=["612 345 678"],
    )
    first_site: SiteBase | None = Field(
        default=None,
        description=(
            "First building of the client, optional. It is created in the "
            "same operation: either both are created, or neither."
        ),
    )


class OrganizationUpdate(OrganizationContact):
    """
    Partial update (admin only): name, contact and billing.

    The status is not changed here: it has its own routes (`/suspend`,
    `/reactivate`, `/extend-trial`), because each status change has its
    own rules. Going to `ACTIVE` is done by the client by subscribing
    (B14).
    """

    name: str | None = Field(default=None, max_length=NAME_MAX)


class OrganizationResponse(ApiModel):
    """
    Fields according to the architecture document (section 5): `id`,
    `name`, `created_at`. B0 added `status` and `trial_ends_at`; B1, the
    contact, the billing and the counters.

    The counters are not stored: they are computed when answering, with
    one `GROUP BY` query each for the whole page.
    """

    id: UUID
    name: str
    status: OrganizationStatus = Field(
        description="TRIAL (7-day trial), ACTIVE or SUSPENDED."
    )
    trial_ends_at: datetime | None = Field(
        default=None,
        description="End of the trial, in UTC. Only for organizations that are or were on trial.",
    )
    city: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    legal_name: str | None = None
    tax_id: str | None = None
    billing_email: str | None = None
    billing_address: str | None = None
    postal_code: str | None = None
    plan: SubscriptionPlan | None = Field(
        default=None,
        description="Plan subscribed from the app (B14). `null` if not subscribed.",
    )
    billing_period: BillingPeriod | None = Field(
        default=None, description="`MONTHLY` or `YEARLY`. `null` if not subscribed."
    )
    contracted_sites: int | None = Field(
        default=None, description="Contracted buildings: also their limit."
    )
    contracted_sensors: int | None = Field(
        default=None, description="Contracted sensors: also their limit."
    )
    monthly_price_eur: int | None = Field(
        default=None, description="Monthly price agreed when subscribing, VAT not included."
    )
    subscribed_at: datetime | None = Field(
        default=None, description="When it subscribed, in UTC."
    )
    iban_masked: str | None = Field(
        default=None, description="Masked only: the full IBAN is not stored."
    )
    sepa_accepted_at: datetime | None = Field(
        default=None, description="When the SEPA direct debit was authorized, in UTC."
    )
    site_count: int = Field(default=0, description="Buildings of the client.")
    sensor_count: int = Field(default=0, description="Sensors in all its buildings.")
    user_count: int = Field(default=0, description="Users of the organization.")
    open_alerts: int = Field(default=0, description="Unresolved alerts.")
    critical_alerts: int = Field(
        default=0, description="Of the unresolved alerts, how many are CRITICAL."
    )
    oldest_open_alert_at: datetime | None = Field(
        default=None,
        description=(
            "When the oldest unresolved alert was created, in UTC. Null if "
            "there is none. Used for \"la más antigua: 6 h\" (oldest: 6 h) "
            "on the admin alerts page."
        ),
    )
    created_at: datetime = Field(description="Creation of the organization, in UTC.")


class OrganizationDelete(ApiRequest):
    """
    Deletion confirmation (B16): the exact name of the organization, as in
    "type the name to confirm". It avoids deleting another one by a wrong
    id.
    """

    confirm_name: str = Field(
        max_length=NAME_MAX,
        description="Name of the organization, exactly (case-sensitive).",
        examples=["Hotel Diagonal Mar"],
    )


class OrganizationDeleted(ApiModel):
    """What was deleted, so the admin sees the scope (B16)."""

    id: UUID
    name: str
    deleted: dict[str, int] = Field(
        description=(
            "Rows deleted per table: readings, alerts, sensors, documents, "
            "sites, invitations, users and organizations."
        ),
        examples=[
            {
                "readings": 5094,
                "alerts": 12,
                "sensors": 8,
                "documents": 2,
                "sites": 3,
                "invitations": 1,
                "users": 4,
                "organizations": 1,
            }
        ],
    )
    detached_admins: int = Field(
        default=0,
        description="Admins that had this organization: they are not deleted, they are left without it.",
    )
    deleted_files: int = Field(
        default=0, description="Document files deleted from disk."
    )
