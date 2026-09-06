# MODEL - sites
# SQLAlchemy model for the sites table
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# Represents a physical site owned by an organization
class Site(Base):
    __tablename__ = "sites"

    # Table-level constraints and validation rules.
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "name",
            name="uq_sites_organization_name",
        ),
        # Latitude must be valid when it is provided.
        CheckConstraint(
            "latitude IS NULL OR latitude BETWEEN -90 AND 90",
            name="ck_sites_latitude",
        ),
        # Longitude must be valid when it is provided.
        CheckConstraint(
            "longitude IS NULL OR longitude BETWEEN -180 AND 180",
            name="ck_sites_longitude",
        ),
    )

    # Auto-generated primary key.
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Required organization that owns this site.
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "organizations.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    # Human-readable site name.
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # Optional physical address.
    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Optional geographic coordinates with fixed decimal precision.
    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )

    # Optional geographic coordinates with fixed decimal precision.
    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(9, 6),
        nullable=True,
    )

    # Creation timestamp managed by the database.
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Last update timestamp managed by SQLAlchemy on updates.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ORM relationship to the parent organization.
    organization: Mapped["Organization"] = relationship(
        "Organization",
        back_populates="sites",
    )

    # Relationship with the sensors installed in this site.
    sensors: Mapped[list["Sensor"]] = relationship(
        "Sensor",
        back_populates="site",
    )
