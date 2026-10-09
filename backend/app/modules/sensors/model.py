# MODEL - sensors
# SQLAlchemy model for the sensors table
from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

"""
Defines the Sensor ORM entity, its database constraints, and its relationships
with sites and readings.
"""

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
            "low_threshold < high_threshold",
            name="ck_sensors_threshold_order",
        ),
        # Same bar range as PRESSURE_MIN_BAR / PRESSURE_MAX_BAR in schemas.py.
        CheckConstraint(
            "low_threshold >= 0 AND high_threshold <= 25",
            name="ck_sensors_threshold_range",
        ),
        CheckConstraint(
            "sensor_type IN ('PRESSURE', 'FLOW')",
            name="ck_sensors_type",
        ),
    )

    # Auto-generated primary key
    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    # Required site where the sensor is installed
    site_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
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
        # Same max length as SensorBase.name in schemas.py.
        String(120),
        nullable=False,
    )

    # Optional zone of the building, for example "Sala técnica"
    location: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    # Floor of the building: 0 is the ground floor, negative are basements
    floor: Mapped[int] = mapped_column(
        Integer,
        server_default="0",
        nullable=False,
    )

    # Measured magnitude: PRESSURE or FLOW
    sensor_type: Mapped[str] = mapped_column(
        String(20),
        server_default="PRESSURE",
        nullable=False,
    )

    # Measurement unit, for example "bar"
    unit: Mapped[str] = mapped_column(
        String(20),
        server_default="bar",
        nullable=False,
    )

    # Required lower pressure threshold
    low_threshold: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )

    # Required higher pressure threshold
    high_threshold: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
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

    readings: Mapped[list["Reading"]] = relationship(
        "Reading",
        back_populates="sensor",
    )

    alerts: Mapped[list["Alert"]] = relationship(
        "Alert",
        back_populates="sensor",
    )
