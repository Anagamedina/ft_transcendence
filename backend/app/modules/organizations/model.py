# MODEL - organizations
# SQLAlchemy model for organizations table
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    __table_args__ = (
        # Same values as OrganizationStatus in the common contract (B0).
        CheckConstraint(
            "status IN ('TRIAL', 'ACTIVE', 'SUSPENDED')",
            name="ck_organizations_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name: Mapped[str] = mapped_column(
        # Same max length as OrganizationCreate.name in schemas.py.
        String(120),
        nullable=False,
    )

    # TRIAL, ACTIVE or SUSPENDED. Existing organizations are ACTIVE.
    status: Mapped[str] = mapped_column(
        String(20),
        server_default="ACTIVE",
        nullable=False,
    )

    # Only set for TRIAL organizations created by the public sign-up.
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Contact data shown in the admin views.
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(320), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # Billing data.
    legal_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tax_id: Mapped[str | None] = mapped_column(String(30), nullable=True)
    billing_email: Mapped[str | None] = mapped_column(String(320), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ORM relationship with the parent site
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="organization",
    )

    # Organization.sites <-> Site.organization
    sites: Mapped[list["Site"]] = relationship(
        "Site",
        back_populates="organization",
    )

    # Organization.invitations <-> Invitation.organization
    # passive_deletes: the database deletes them (ON DELETE CASCADE); the ORM
    # does not load them or try to set organization_id to NULL.
    invitations: Mapped[list["Invitation"]] = relationship(
        "Invitation",
        back_populates="organization",
        passive_deletes=True,
    )


# Names are unique ignoring case: "Hotel Sol" and "hotel sol" collide.
# Declared after the class so the expression can reference the column.
Index(
    "uq_organizations_name_lower",
    func.lower(Organization.name),
    unique=True,
)
