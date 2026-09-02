# MODEL - sensors
# SQLAlchemy model for the sensors table
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# Represents a sensor installed in a site
class Sensor(Base):
    __tablename__ = "sensors"

    __table_args__ = (
        # the external sensor ID must be unique within the same site.
        UniqueConstraint(
            "site_id",
            "external_id",
            name="uq_sensors_site_external_id",
        ),
        # The lower threshold must be lower than the higher threshold.
        CheckConstraint(
            "low_threshold IS NULL "
            "OR high_threshold IS NULL "
            "OR low_threshold < high_threshold",
            name="ck_sensors_threshold_order",
        ),
    )

    # Auto-generated primary key
    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    # Required site where the sensor is installed
    site_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "sites.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    # Identifier provided by the physical sensor or manufacturer
    external_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Human-readable sensor name
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # Measurement unit, for example "bar"
    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Optional lower pressure threshold
    low_threshold: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )

    # Optional higher pressure threshold
    high_threshold: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 3),
        nullable=True,
    )

    # Indicates whether the sensor is active
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default="true",
        nullable=False,
    )

    # Sensor creation timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Timestamp of the last update
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ORM relationship with the parent site
    site: Mapped["Site"] = relationship(
        "Site",
        back_populates="sensors",
    )
