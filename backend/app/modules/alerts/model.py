# MODEL - alerts
# Entidad/es SQLAlchemy de este dominio.

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    __table_args__ = (
        CheckConstraint(
            "alert_type IN ('LOW', 'HIGH', 'OFFLINE')",
            name="ck_alerts_type",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED')",
            name="ck_alerts_status",
        ),
        CheckConstraint(
            "severity IN ('INFO', 'WARNING', 'CRITICAL')",
            name="ck_alerts_severity",
        ),
        Index(
            "ix_alerts_sensor_created_at",
            "sensor_id",
            "created_at",
        ),
        Index(
            "ix_alerts_status_created_at",
            "status",
            "created_at",
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

    alert_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    sensor: Mapped["Sensor"] = relationship(
        "Sensor",
        back_populates="alerts",
    )