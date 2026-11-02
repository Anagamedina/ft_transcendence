# SCHEMAS — invitations
# Pydantic request/response (OpenAPI contract). Never return a raw ORM model.
"""
Invitations contract (B4, issue #141).

It was published before the routes, as in #23, so the frontend (F6 by
Florinda and F11 by Eduardo) could build its screens with mocks. The
routes:

    POST   /api/invitations                       admin  → InvitationSentResponse (201)
    GET    /api/invitations                       admin  → Page[InvitationResponse]
    DELETE /api/invitations/{id}                  admin  → 204 (revocar)
    POST   /api/invitations/{id}/resend           admin  → InvitationSentResponse
    GET    /api/invitations/by-code/{code}        public → InvitationPublicResponse
    POST   /api/invitations/by-code/{code}/accept public → SessionResponse (201)

The two public routes start with `/api/invitations/by-code/` on purpose:
it is what the gateway rate-limits per IP (I11, PR #199).

**The code only shows once**: in the response of the creation and of the
resend. The database stores its hash (D3), so it cannot be shown again
later; that is why `InvitationResponse` does not have it.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.shared.enums import InvitationStatus
from app.shared.schemas import ApiModel, ApiRequest, Password


class InvitationCreate(ApiRequest):
    """Invite an email to an existing organization (admin)."""

    email: EmailStr = Field(
        description="Who is invited. Stored in lowercase.",
        examples=["nuevo.gestor@hotelmar.com"],
    )
    organization_id: UUID = Field(
        description="Organization it will join on accepting.",
        examples=["11111111-1111-4111-8111-111111111111"],
    )


class InvitationResponse(ApiModel):
    """An invitation in the admin list. Without the code."""

    id: UUID
    organization_id: UUID
    organization_name: str = Field(examples=["Hotel Mar"])
    email: EmailStr = Field(examples=["nuevo.gestor@hotelmar.com"])
    status: InvitationStatus = Field(
        description="Computed from the dates: see `InvitationStatus`.",
        examples=["PENDING"],
    )
    expires_at: datetime = Field(
        description="Expires after `INVITATION_TTL_DAYS` days (7 by default), in UTC."
    )
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None
    created_by_name: str | None = Field(
        default=None,
        description="Who sent it. Null if that user no longer exists.",
        examples=["Ana Medina"],
    )
    created_at: datetime


class InvitationSentResponse(InvitationResponse):
    """
    Response of the creation and of the resend: the invitation plus the
    code and the link. **It is the only time they are visible**; the admin
    copies them and passes them on. Resending creates a new code and the
    previous one stops working.
    """

    code: str = Field(
        description="Single-use code. It cannot be retrieved again.",
        examples=["k3Vq9mZt2xR8"],
    )
    url: str = Field(
        description=(
            "Link to accept: `PUBLIC_BASE_URL` + `/registro?invitacion={code}`, "
            "the route F6 reads."
        ),
        examples=["https://localhost/registro?invitacion=k3Vq9mZt2xR8"],
    )


class InvitationPublicResponse(ApiModel):
    """
    What whoever opens the link sees, without a session: just enough for
    the accept form. An expired invitation answers 410
    `INVITATION_EXPIRED`; an accepted, revoked or missing one, 404
    `INVITATION_NOT_FOUND`.
    """

    organization_name: str = Field(examples=["Hotel Mar"])
    email: EmailStr = Field(examples=["nuevo.gestor@hotelmar.com"])
    expires_at: datetime


class InvitationAccept(ApiRequest):
    """
    Accept the invitation: creates the `client` user in the organization
    and opens the session, like the sign-up. The email is not chosen: it
    is the invitation one.
    """

    name: str = Field(min_length=1, max_length=120, examples=["Laura Puig"])
    password: Password = Field(
        max_length=128,
        description=(
            "Same rule as the sign-up (B10): at least 12 characters, not "
            "common and not containing the email. Otherwise, 422 "
            "`WEAK_PASSWORD`."
        ),
        examples=["agua-que-no-se-escapa"],
    )
    accept_terms: bool = Field(
        description="Must be `true`. Otherwise, 422 `TERMS_NOT_ACCEPTED`.",
        examples=[True],
    )
