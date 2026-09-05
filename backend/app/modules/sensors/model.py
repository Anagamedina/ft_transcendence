# MODEL - sensors
# SQLAlchemy model for the sensors table
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# Represents a sensor installed in a site
class Sensor(Base):
    __tablename__ = "sensors"

    __table_args__ = (
        # Both thresholds are mandatory, so the check needs no NULL guards.
        CheckConstraint(
            "min_pressure < max_pressure",
            name="ck_sensors_pressure_order",
        ),
        # Same range as PRESSURE_MIN_BAR / PRESSURE_MAX_BAR in schemas.py.
        # Both layers must agree on it.
        CheckConstraint(
            "min_pressure >= 0 AND max_pressure <= 25",
            name="ck_sensors_pressure_range",
        ),
        # Mirrors the SensorType enum of the API contract.
        CheckConstraint(
            "sensor_type IN ('PRESSURE', 'FLOW')",
            name="ck_sensors_type",
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

    # Human-readable sensor name
    name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )

    # Zone of the building where the sensor is installed
    location: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )

    # Measured magnitude. PRESSURE is the one the MVP works with
    sensor_type: Mapped[str] = mapped_column(
        String(20),
        server_default="PRESSURE",
        nullable=False,
    )

    # Lower pressure threshold in bar. Below it, a LOW_PRESSURE alert is raised
    min_pressure: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )

    # Higher pressure threshold in bar. Above it, a HIGH_PRESSURE alert is raised
    max_pressure: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )

    # Last time a reading arrived from this sensor. NULL if it never sent one.
    # SENSOR_OFFLINE is derived from this column, so the status itself is not
    # stored: a stored status would need a background job to keep it fresh.
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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
