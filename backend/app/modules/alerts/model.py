# MODEL - alerts
# Entidad/es SQLAlchemy de este dominio.

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Alert(Base):
    __tablename__ = "alerts"

    __table_args__ = (
        CheckConstraint(
            "alert_type IN ('LOW_PRESSURE', 'HIGH_PRESSURE', 'SENSOR_OFFLINE')",
            name="ck_alerts_type",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'RESOLVED')",
            name="ck_alerts_status",
        ),
        CheckConstraint(
            "severity IN ('WARNING', 'CRITICAL')",
            name="ck_alerts_severity",
        ),
        Index(
            "ix_alerts_sensor_created_at",
            "sensor_id",
            "created_at",
        ),
        # Alert list by status, newest first. Kept next to the severity one:
        # without it, a list filtered only by status has to sort every row
        # (EXPLAIN ANALYZE, 200k alerts: history from 0.3 ms to 308 ms).
        Index(
            "ix_alerts_status_created_at",
            "status",
            "created_at",
        ),
        # D5: same list filtered by severity too (WARNING / CRITICAL).
        Index(
            "ix_alerts_status_severity_created_at",
            "status",
            "severity",
            "created_at",
        ),
        # D5: the open alert of a sensor, looked up on every reading.
        Index(
            "ix_alerts_sensor_status",
            "sensor_id",
            "status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )

    sensor_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
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
    message: Mapped[str] = mapped_column(
        String(255),
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

    # Who acknowledged / resolved the alert. NULL if it was automatic or the
    # user was deleted: the alert history is kept.
    acknowledged_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            name="fk_alerts_acknowledged_by_users",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    resolved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey(
            "users.id",
            name="fk_alerts_resolved_by_users",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    acknowledged_by_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[acknowledged_by],
    )
    resolved_by_user: Mapped["User | None"] = relationship(
        "User", foreign_keys=[resolved_by],
    )

    sensor: Mapped["Sensor"] = relationship(
        "Sensor",
        back_populates="alerts",
    )
