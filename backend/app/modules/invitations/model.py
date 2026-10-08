# MODEL - invitations
# SQLAlchemy model for the invitations table
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# An invitation for an email to join an existing organization. The public
# sign-up, which creates a new organization, is B10 and does not use it.
#
# States, derived from the timestamps:
#   pending  -> accepted_at IS NULL AND revoked_at IS NULL
#   accepted -> accepted_at IS NOT NULL
#   revoked  -> revoked_at IS NOT NULL
#   expired  -> pending and expires_at < now() (checked by the service)
class Invitation(Base):
    __tablename__ = "invitations"

    __table_args__ = (
        UniqueConstraint("code_hash", name="uq_invitations_code_hash"),
        # Stored normalized, like users.email (normalize_email in
        # users/repository.py). The DB rejects anything else so the unique
        # index below cannot be bypassed with "Ana@x.com" vs "ana@x.com".
        CheckConstraint(
            "email = lower(email)",
            name="ck_invitations_email_lowercase",
        ),
        # An invitation ends once: accepted or revoked, never both.
        CheckConstraint(
            "accepted_at IS NULL OR revoked_at IS NULL",
            name="ck_invitations_accepted_or_revoked",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Deleting the organization deletes its invitations.
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "organizations.id",
            name="fk_invitations_organization_id_organizations",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    # Same length as users.email.
    email: Mapped[str] = mapped_column(
        String(320),
        nullable=False,
    )

    # Hash of the code sent by email; the code itself is never stored.
    # 64 = SHA-256 in hex.
    code_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Who sent it. NULL if that user was deleted: the invitation is kept.
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            name="fk_invitations_created_by_users",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Invitation.organization <-> Organization.invitations
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="invitations",
    )


# Only one pending invitation per email and organization. Expired ones still
# count: the index cannot use now(), so the service revokes the old invitation
# before sending a new one.
Index(
    "uq_invitations_pending_org_email",
    Invitation.organization_id,
    Invitation.email,
    unique=True,
    postgresql_where=text("accepted_at IS NULL AND revoked_at IS NULL"),
    sqlite_where=text("accepted_at IS NULL AND revoked_at IS NULL"),
)
