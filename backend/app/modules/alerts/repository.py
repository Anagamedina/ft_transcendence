# REPOSITORY — alerts
# Acceso a datos (SQLAlchemy queries). Filtrar siempre por organización.
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.alerts.model import Alert
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site

class AlertRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
            self,
            sensor_id: UUID,
            alert_type: str,
            severity: str,
            message: str,
    ) -> Alert:
        alert = Alert(
            sensor_id=sensor_id,
            alert_type=alert_type,
            severity=severity,
            message=message,
            status="ACTIVE",
        )
        self.db.add(alert)
        try:
            self.db.flush()
        except SQLAlchemyError:
            self.db.rollback()
            raise
        return alert

    def get_by_id(
            self,
            alert_id: UUID,
            organization_id: UUID) -> Alert | None:
        query = (
            select(Alert).join(Sensor).join(Site)
            .where(Alert.id == alert_id, Site.organization_id == organization_id)
        )
        return self.db.scalar(query)

    def list_by_organization(
            self, organization_id: UUID, status: str | None = None,
            sensor_id: UUID | None = None,
            offset: int = 0, limit: int = 100,
    ) -> tuple[list[Alert], int]:
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        query = (
            select(Alert).join(Sensor).join(Site)
            .where(Site.organization_id == organization_id)
        )
        if status is not None:
            query = query.where(Alert.status == status)
        if sensor_id is not None:
            query = query.where(Alert.sensor_id == sensor_id)

        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = list(self.db.scalars(
            query.order_by(Alert.created_at.desc()).offset(offset).limit(limit)
        ).all())
        return items, int(total or 0)

    def acknowledge(self, alert_id: UUID, when: datetime) -> Alert | None:
        alert = self.db.get(Alert, alert_id)
        if alert is None:
            return None
        if alert.acknowledged_at is None:
            alert.acknowledged_at = when
        return alert

    def resolve(self, alert_id: UUID, when: datetime) -> Alert | None:
        alert = self.db.get(Alert, alert_id)
        if alert is None:
            return None
        alert.status = "RESOLVED"
        alert.resolved_at = when
        return alert