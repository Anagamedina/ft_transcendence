# REPOSITORY — analytics
# Acceso a datos (SQLAlchemy queries). Filtrar siempre por organización.
"""
Agregados por sensor y día para la exportación (issue #134, B18).

Todo se agrega en la base de datos (GROUP BY): nunca se cargan las
lecturas una a una, que en un año pueden ser millones.

Los días van en UTC: `date()` usa la zona horaria de la sesión, que en el
contenedor de PostgreSQL es UTC.

`organization_id=None` significa TODAS las organizaciones (admin), como en
el resto de repositories. Lo decide `get_org_scope`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.modules.alerts.model import Alert
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site


@dataclass(frozen=True)
class ReadingDay:
    sensor_id: UUID
    day: str
    count: int
    minimum: Decimal
    average: Decimal
    maximum: Decimal


@dataclass(frozen=True)
class AlertDay:
    sensor_id: UUID
    day: str
    total: int
    critical: int
    resolved: int


@dataclass(frozen=True)
class SensorInfo:
    sensor_id: UUID
    organization: str
    site: str
    external_id: str
    name: str
    unit: str


def _day(column):
    # date() exists in PostgreSQL and SQLite. PostgreSQL returns a date and
    # SQLite a 'YYYY-MM-DD' string; str() leaves both the same.
    return func.date(column)


class AnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _scoped(self, query, organization_id: UUID | None):
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        return query

    def readings_by_sensor_and_day(
        self, organization_id: UUID | None, start: datetime, end: datetime
    ) -> list[ReadingDay]:
        day = _day(Reading.recorded_at)
        query = (
            select(
                Reading.sensor_id,
                day,
                func.count(),
                func.min(Reading.value),
                func.avg(Reading.value),
                func.max(Reading.value),
            )
            .join(Sensor, Sensor.id == Reading.sensor_id)
            .join(Site, Site.id == Sensor.site_id)
            .where(Reading.recorded_at >= start, Reading.recorded_at < end)
            .group_by(Reading.sensor_id, day)
        )
        rows = self.db.execute(self._scoped(query, organization_id)).all()
        return [
            ReadingDay(sensor_id, str(d), count, Decimal(mn), Decimal(av), Decimal(mx))
            for sensor_id, d, count, mn, av, mx in rows
        ]

    def alerts_by_sensor_and_day(
        self, organization_id: UUID | None, start: datetime, end: datetime
    ) -> list[AlertDay]:
        day = _day(Alert.created_at)
        query = (
            select(
                Alert.sensor_id,
                day,
                func.count(),
                func.sum(case((Alert.severity == "CRITICAL", 1), else_=0)),
                func.sum(case((Alert.status == "RESOLVED", 1), else_=0)),
            )
            .join(Sensor, Sensor.id == Alert.sensor_id)
            .join(Site, Site.id == Sensor.site_id)
            .where(Alert.created_at >= start, Alert.created_at < end)
            .group_by(Alert.sensor_id, day)
        )
        rows = self.db.execute(self._scoped(query, organization_id)).all()
        return [
            AlertDay(sensor_id, str(d), total, int(critical or 0), int(resolved or 0))
            for sensor_id, d, total, critical, resolved in rows
        ]

    def sensors(self, sensor_ids: set[UUID]) -> dict[UUID, SensorInfo]:
        if not sensor_ids:
            return {}
        rows = self.db.execute(
            select(
                Sensor.id,
                Organization.name,
                Site.name,
                Sensor.external_id,
                Sensor.name,
                Sensor.unit,
            )
            .join(Site, Site.id == Sensor.site_id)
            .join(Organization, Organization.id == Site.organization_id)
            .where(Sensor.id.in_(sensor_ids))
        ).all()
        return {row[0]: SensorInfo(*row) for row in rows}
