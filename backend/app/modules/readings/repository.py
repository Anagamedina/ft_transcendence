"""Organization-scoped persistence queries for readings and history."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site


class ReadingRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        sensor_id: UUID,
        value: float,
        unit: str,
        recorded_at: datetime,
    ) -> Reading:
        reading = Reading(
            sensor_id=sensor_id,
            value=value,
            unit=unit,
            recorded_at=recorded_at,
        )
        self.db.add(reading)
        try:
            self.db.flush()
        except SQLAlchemyError:
            self.db.rollback()
            raise

        return reading

    def list_by_sensor(
        self,
        sensor_id: UUID,
        organization_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Reading], int]:
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        query = (
            select(Reading)
            .join(Sensor, Reading.sensor_id == Sensor.id)
            .join(Site, Sensor.site_id == Site.id)
            .where(
                Reading.sensor_id == sensor_id,
                Site.organization_id == organization_id,
            )
        )
        total = self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )

        items = list(
            self.db.scalars(
                query.order_by(Reading.recorded_at, Reading.id)
                .offset(offset)
                .limit(limit)
            ).all()
        )

        return items, int(total or 0)
