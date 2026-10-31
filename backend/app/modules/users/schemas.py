# SCHEMAS — users
# Pydantic request/response (OpenAPI contract). Never return a raw ORM model.
"""
Users contract (issue #23).

The key point of this file is the split between what comes in and what
goes out:

    PasswordChange → passwords        (they come in, never go out)
    UserResponse   → no password or hash

It is tempting to declare a single `User` and reuse it in both
directions. It is not done because the day the model gains a
`password_hash` or `reset_token` field, that field would show up in the
API response on its own. With separate schemas that cannot happen:
`UserResponse` only copies the fields it declares.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import EmailStr, Field

from app.shared.enums import (
    BillingPeriod,
    BuildingType,
    OrganizationStatus,
    SubscriptionPlan,
)
from app.shared.schemas import ApiModel, ApiRequest, Password, RawPassword


class UserRole(str, Enum):
    """
    Role inside the application.

    It inherits from `str` so it serializes as `"admin"` and not as
    `"UserRole.ADMIN"`, and so it can be compared with a string without
    converting. In OpenAPI it shows up as a string enum, which is what the
    frontend needs to draw the selector.

    - `admin`  → manages organizations, sites and sensors.
    - `client` → only sees the data of its own organization.
    """

    ADMIN = "admin"
    CLIENT = "client"


class UserUpdate(ApiRequest):
    """
    Partial update. Every field is optional.

    `None` and "field missing" mean different things: to know which ones
    the client touched, use `model_dump(exclude_unset=True)`, not
    `exclude_none`.
    """

    name: str | None = Field(default=None, min_length=1, max_length=120)
    role: UserRole | None = None
    # B6 (#141): move or add a user to an organization. A `client` always
    # needs one (CHECK `ck_users_client_has_organization`). The email is
    # not editable: it is not here, and `extra="forbid"` rejects it.
    organization_id: UUID | None = Field(
        default=None,
        description="Organization of the user. Mandatory if it stays a `client`.",
    )


class UserResponse(ApiModel):
    """
    User as the client sees it.

    Fields according to the domain model of the architecture document
    (section 5): `id`, `organization_id`, `name`, `email`, `role`,
    `created_at`. `password_hash` exists in the table and does NOT appear
    here: that is exactly what the input/output split guarantees.
    """

    id: UUID = Field(description="User id.")
    email: EmailStr
    name: str
    role: UserRole
    organization_id: UUID | None = Field(
        default=None,
        description=(
            "Organization it belongs to. Null for a global admin, who is "
            "not tied to any."
        ),
    )
    created_at: datetime = Field(description="Creation of the user, in UTC.")


# ---------------------------------------------------------
# B6 AND B8 CONTRACT (#141, #144)
# ---------------------------------------------------------
# Published before the routes, as in #23, so the frontend (F11 and F13 by
# Eduardo and Lylia) could build its screens with mocks.
#
# B6 — users (admin):
#   GET    /api/users?organization_id=&q=&active=  → Page[UserAdminResponse]
#   GET    /api/users/{id}                         → UserAdminResponse
#   PATCH  /api/users/{id}                         → UserAdminResponse (UserUpdate)
#   POST   /api/users/{id}/deactivate              → UserAdminResponse
#   POST   /api/users/{id}/activate                → UserAdminResponse
#   DELETE /api/users/{id}                         → 204
#
# B8 — My account (anyone with a session):
#   GET    /api/me                → MeResponse
#   PATCH  /api/me                → MeResponse (MeUpdate)
#   POST   /api/me/password       → MessageResponse (PasswordChange)
class UserAdminResponse(UserResponse):
    """A user in the admin user management (B6)."""

    organization_name: str | None = Field(
        default=None, description="Name of its organization.", examples=["Hotel Mar"]
    )
    is_active: bool = Field(
        default=True,
        description=(
            "`false` if an admin has deactivated it: it cannot log in (403 "
            "`ACCOUNT_DISABLED`)."
        ),
    )
    last_login_at: datetime | None = Field(
        default=None, description="Last login, in UTC. Null if it never logged in."
    )


class OrganizationSummary(ApiModel):
    """The organization of the session holder, for My account (B8)."""

    id: UUID
    name: str = Field(examples=["Hotel Mar"])
    status: OrganizationStatus = Field(examples=["TRIAL"])
    trial_ends_at: datetime | None = Field(
        default=None, description="End of the trial, in UTC. Null if not on trial."
    )


class MeResponse(ApiModel):
    """
    Response of `GET /api/me` since B8. It keeps `user` where it was (the
    frontend already reads it like that) and adds the My account data.
    """

    user: UserResponse
    organization: OrganizationSummary | None = Field(
        default=None, description="Null for an admin without an organization."
    )
    last_login_at: datetime | None = None
    terms_version: str | None = Field(
        default=None,
        description="Version of the terms it accepted. Null for accounts older than B10.",
        examples=["2026-10"],
    )
    terms_accepted_at: datetime | None = None
    deletion_requested_at: datetime | None = Field(
        default=None,
        description="When it requested deletion (B15), in UTC. Null if it has not.",
    )


class CurrentSessionResponse(ApiModel):
    """Response of `GET /api/me/session`: the user, or `null` without a session."""

    user: MeResponse | None = Field(
        default=None, description="The same as `GET /api/me`, or null without a session."
    )


class MeUpdate(ApiRequest):
    """What each user can change in their account (B8). Not the email."""

    name: str = Field(min_length=1, max_length=120, examples=["Ana Medina"])


class PasswordChange(ApiRequest):
    """
    Change your own password (B8). If `current_password` does not match,
    422 `WRONG_PASSWORD` (not 401: the session is still valid, and a 401
    would make the frontend close it); if the new one breaks the B10 rule,
    422 `WEAK_PASSWORD`. Other open sessions are not closed (it would need
    a column that does not exist).
    """

    # Compared as is, without trimming: same as login.
    current_password: RawPassword = Field(min_length=1, max_length=128)
    new_password: Password = Field(
        max_length=128,
        description="Same rule as the sign-up (B10): at least 12 characters, not common, without the email.",
        examples=["agua-que-no-se-escapa"],
    )


# ---------------------------------------------------------
# B15 — EXPORT MY DATA AND REQUEST DELETION (#149)
# ---------------------------------------------------------
#   GET  /api/me/export            → MyDataExport (downloaded as .json)
#   POST /api/me/deletion-request  → DeletionRequestResponse
#
# The export schemas are their own, not `SiteResponse` nor
# `OrganizationResponse`: they only hold what is stored (no counters or
# computed states) and do not change if the screens change.
class AccountExport(ApiModel):
    """The account of whoever exports. Without `password_hash`, like `UserResponse`."""

    id: UUID
    email: EmailStr
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None
    terms_version: str | None = Field(
        default=None,
        description="Version of the terms it accepted (B10). Null for older accounts.",
        examples=["2026-10"],
    )
    terms_accepted_at: datetime | None = None
    deletion_requested_at: datetime | None = None


class OrganizationExport(ApiModel):
    """The organization as it is stored. The IBAN, masked only."""

    id: UUID
    name: str
    status: OrganizationStatus
    trial_ends_at: datetime | None = None
    city: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    legal_name: str | None = None
    tax_id: str | None = None
    billing_email: str | None = None
    billing_address: str | None = None
    postal_code: str | None = None
    plan: SubscriptionPlan | None = None
    billing_period: BillingPeriod | None = None
    contracted_sites: int | None = None
    contracted_sensors: int | None = None
    monthly_price_eur: int | None = None
    subscribed_at: datetime | None = None
    iban_masked: str | None = None
    sepa_accepted_at: datetime | None = None
    created_at: datetime


class SiteExport(ApiModel):
    """A building of the organization, with what is stored."""

    id: UUID
    name: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    district: str | None = None
    floors: int
    basements: int
    building_type: BuildingType
    created_at: datetime


class MyDataExport(ApiModel):
    """
    Everything AquaGuard stores about the account (B15): the account, its
    organization and its buildings. An admin without an organization gets
    a null `organization` and an empty `sites`, not everyone's buildings.
    """

    exported_at: datetime = Field(description="When it was generated, in UTC.")
    current_terms_version: str = Field(
        description=(
            "Current version of the terms. If it does not match "
            "`account.terms_version`, the account accepted older ones."
        ),
        examples=["2026-10"],
    )
    account: AccountExport
    organization: OrganizationExport | None = None
    sites: list[SiteExport] = Field(default_factory=list)


class DeletionRequestResponse(ApiModel):
    """Deletion request recorded (B15). Nothing is deleted yet."""

    deletion_requested_at: datetime = Field(
        description="When it was first requested, in UTC. Repeating the request does not change it."
    )
    message: str = Field(
        examples=["Hemos registrado tu petición de baja. Un administrador la tramitará."]
    )
