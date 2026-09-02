# MODEL — readings
# Entidad/es SQLAlchemy de este dominio.
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Reading(Base):
    __tablename__ = "readings"

    __table_args__ = (
        Index(
            "ix_readings_sensor_recorded_at",
            "sensor_id",
            "recorded_at",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True,
    )

    sensor_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "sensors.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    value: Mapped[Decimal] = mapped_column(
        Numeric(10, 3),
        nullable=False,
    )

    unit: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    sensor: Mapped["Sensor"] = relationship(
        "Sensor",
        back_populates="readings",
    )