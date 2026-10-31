# SCHEMAS — subscriptions
# Pydantic request/response (OpenAPI contract). Never return a raw ORM model.
"""
Subscription contract (B14, issue #150).

    GET  /api/plans                      → list[PlanResponse]
    POST /api/me/organization/subscribe  → SubscriptionRequest → SubscriptionResponse

The tax id, the postal code, the phone and the IBAN are validated in the
service (`app/shared/fields.py`), not in the schema, to answer with their
own code (`INVALID_TAX_ID`, `INVALID_POSTAL_CODE`, `INVALID_PHONE`,
`INVALID_IBAN`) instead of the generic `VALIDATION_ERROR`, like the B1
`INVALID_NAME`.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.modules.subscriptions.plans import MAX_SITES
from app.shared.enums import BillingPeriod, OrganizationStatus, SubscriptionPlan
from app.shared.schemas import ApiModel, ApiRequest

# Form caps. Buildings: the Empresa plan maximum; more than that is a
# custom quote.
MAX_CONTRACT_SITES = MAX_SITES
MAX_CONTRACT_SENSORS = 1000


class PlanResponse(ApiModel):
    """A plan of the catalog. `None` in the limits means "no limit"."""

    id: SubscriptionPlan
    name: str = Field(examples=["Profesional"])
    description: str
    monthly_price_eur: int = Field(
        description="Monthly plan base in euros, VAT not included. Each sensor is added on top."
    )
    sensor_price_eur: int = Field(description="Monthly price of each sensor, in euros.")
    yearly_months: int = Field(description="Months paid with the yearly payment.")
    max_sites: int | None = Field(
        description="Up to how many buildings the plan covers. It decides which plan applies."
    )
    max_sensors: int | None = Field(
        description="`null` in all of them today: sensors do not change the plan, they are paid separately."
    )
    features: list[str]


class SubscriptionRequest(ApiRequest):
    """
    What it contracts, tax data and contact of the client leaving the trial.

    It has no plan: it comes from `sites` and `sensors`, and so does the
    price (see `plans.py`). The tax data and the account are mandatory
    because without them it cannot be invoiced or charged. The contact is
    optional: if it does not come, the current one stays.
    """

    sites: int = Field(
        ge=1, le=MAX_CONTRACT_SITES,
        description="Buildings it contracts. Not fewer than it already has.",
        examples=[2],
    )
    sensors: int = Field(
        ge=1, le=MAX_CONTRACT_SENSORS,
        description=(
            "Sensors it contracts. At least one per building and not fewer "
            "than it already has."
        ),
        examples=[12],
    )
    billing_period: BillingPeriod = Field(
        description="`MONTHLY` (every month) or `YEARLY` (ten months in advance)."
    )
    legal_name: str = Field(
        min_length=1, max_length=200, description="Legal company name.",
        examples=["Hoteles Diagonal S.L."],
    )
    tax_id: str = Field(
        min_length=1, max_length=30,
        description="NIF, NIE or CIF. Stored in uppercase without spaces or hyphens.",
        examples=["B12345678"],
    )
    billing_address: str = Field(
        min_length=1, max_length=200, description="Billing address, without the postal code.",
        examples=["Avinguda Diagonal 100"],
    )
    postal_code: str = Field(
        min_length=1, max_length=10, description="Postal code: five digits.",
        examples=["08019"],
    )
    city: str = Field(
        min_length=1, max_length=120, description="City and province.",
        examples=["Barcelona"],
    )
    billing_email: EmailStr = Field(description="Email the invoices are sent to.")
    contact_email: EmailStr | None = Field(default=None)
    phone: str = Field(
        max_length=30,
        description=(
            "Spanish phone, mandatory. Stored as `+34 612 345 678`; if it is "
            "not valid, 422 `INVALID_PHONE`."
        ),
        examples=["612 345 678"],
    )
    iban: str = Field(
        min_length=1,
        max_length=42,
        description=(
            "Account for the direct debit. It is checked and **stored masked "
            "only**: the API never returns it nor stores it whole."
        ),
        examples=["ES91 2100 0418 4502 0005 1332"],
    )
    accept_terms: bool = Field(
        description="Must be `true`: accepts the contract conditions."
    )
    accept_sepa: bool = Field(
        description="Must be `true`: authorizes the SEPA direct debit of the IBAN."
    )


class SubscriptionResponse(ApiModel):
    """The organization already as a client, with what was stored."""

    organization_id: UUID
    organization_name: str
    status: OrganizationStatus
    plan: SubscriptionPlan
    plan_name: str = Field(examples=["Básico"])
    billing_period: BillingPeriod
    contracted_sites: int = Field(examples=[2])
    contracted_sensors: int = Field(examples=[12])
    monthly_price_eur: int = Field(
        description="Monthly price: plan base plus each sensor, VAT not included.",
        examples=[149],
    )
    billed_price_eur: int = Field(
        description="What is charged each time: the month, or ten months if yearly.",
        examples=[149],
    )
    subscribed_at: datetime = Field(description="Time of the subscription, in UTC.")
    legal_name: str
    tax_id: str
    billing_address: str
    postal_code: str
    city: str
    billing_email: str
    contact_email: str | None = None
    phone: str | None = None
    iban_masked: str = Field(examples=["ES** **** **** **** **** 1332"])
    sepa_accepted_at: datetime = Field(
        description="When the direct debit was authorized, in UTC."
    )
