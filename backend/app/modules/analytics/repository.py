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
from datetime import date, datetime, timedelta, timezone
from statistics import median
from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, exists, func, select
from sqlalchemy.orm import Session

from app.modules.alerts.model import Alert
from app.modules.organizations.model import Organization
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.sensors.status import OFFLINE_TRAS
from app.shared.enums import AlertStatus


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

    def overview(self, organization_id: UUID | None, is_admin: bool) -> dict:
        """Return KPI aggregates without materialising readings or alerts."""
        site_scope = select(Site.id)
        if organization_id is not None:
            site_scope = site_scope.where(Site.organization_id == organization_id)

        sites_total = self.db.scalar(
            select(func.count()).select_from(site_scope.subquery())
        ) or 0
        sensors_scope = select(Sensor.id).join(Site, Site.id == Sensor.site_id)
        if organization_id is not None:
            sensors_scope = sensors_scope.where(Site.organization_id == organization_id)
        sensors_total = self.db.scalar(
            select(func.count()).select_from(sensors_scope.subquery())
        ) or 0

        cutoff = datetime.now(timezone.utc) - OFFLINE_TRAS
        online_exists = exists(
            select(Reading.id).where(
                Reading.sensor_id == Sensor.id,
                Reading.created_at >= cutoff,
            )
        )
        online_query = select(func.count()).select_from(Sensor).join(
            Site, Site.id == Sensor.site_id
        ).where(online_exists)
        if organization_id is not None:
            online_query = online_query.where(Site.organization_id == organization_id)
        sensors_online = self.db.scalar(online_query) or 0

        alerts_query = select(
            func.count(Alert.id),
            func.sum(case((Alert.severity == "CRITICAL", 1), else_=0)),
        ).join(Sensor, Sensor.id == Alert.sensor_id).join(Site, Site.id == Sensor.site_id).where(
            Alert.status == AlertStatus.ACTIVE.value
        )
        if organization_id is not None:
            alerts_query = alerts_query.where(Site.organization_id == organization_id)
        open_alerts, critical_open_alerts = self.db.execute(alerts_query).one()

        organizations_total = None
        organizations_needing_attention = None
        if is_admin:
            organizations_total = self.db.scalar(select(func.count(Organization.id))) or 0
            needing = (
                select(func.count(func.distinct(Site.organization_id)))
                .join(Sensor, Sensor.site_id == Site.id)
                .join(Alert, Alert.sensor_id == Sensor.id)
                .where(Alert.status == AlertStatus.ACTIVE.value)
            )
            organizations_needing_attention = self.db.scalar(needing) or 0

        median_minutes = self._median_resolution_minutes(organization_id)
        return {
            "organizations_total": int(organizations_total) if organizations_total is not None else None,
            "organizations_needing_attention": int(organizations_needing_attention)
            if organizations_needing_attention is not None else None,
            "sites_total": int(sites_total),
            "sensors_total": int(sensors_total),
            "sensors_online": int(sensors_online),
            "open_alerts": int(open_alerts or 0),
            "critical_open_alerts": int(critical_open_alerts or 0),
            "median_resolution_minutes": median_minutes,
        }

    def _median_resolution_minutes(self, organization_id: UUID | None) -> float | None:
        start = datetime.now(timezone.utc) - timedelta(days=30)
        duration = func.extract(
            "epoch", Alert.resolved_at - Alert.created_at
        ) / 60.0
        query = (
            select(func.percentile_cont(0.5).within_group(duration))
            .join(Sensor, Sensor.id == Alert.sensor_id)
            .join(Site, Site.id == Sensor.site_id)
            .where(
                Alert.status == AlertStatus.RESOLVED.value,
                Alert.resolved_at.is_not(None),
                Alert.created_at >= start,
            )
        )
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)

        if self.db.bind.dialect.name == "postgresql":
            value = self.db.scalar(query)
            return float(value) if value is not None else None

        # SQLite is used by the fast test suite and has no percentile_cont.
        fallback = self.db.execute(
            select(Alert.created_at, Alert.resolved_at)
            .join(Sensor, Sensor.id == Alert.sensor_id)
            .join(Site, Site.id == Sensor.site_id)
            .where(
                Alert.status == AlertStatus.RESOLVED.value,
                Alert.resolved_at.is_not(None),
                Alert.created_at >= start,
                *( [Site.organization_id == organization_id] if organization_id is not None else [] ),
            )
        ).all()
        if not fallback:
            return None
        return float(median((resolved - created).total_seconds() / 60 for created, resolved in fallback))

    def site_weekly_alerts(
        self, site_id: UUID, week_start: date, organization_id: UUID | None
    ) -> dict | None:
        site_query = select(Site.id, Site.name).where(Site.id == site_id)
        if organization_id is not None:
            site_query = site_query.where(Site.organization_id == organization_id)
        site = self.db.execute(site_query).one_or_none()
        if site is None:
            return None

        sensors = self.db.execute(
            select(Sensor.id, Sensor.name, Sensor.floor)
            .where(Sensor.site_id == site_id)
            .order_by(Sensor.name, Sensor.id)
        ).all()
        start = datetime.combine(week_start, datetime.min.time(), tzinfo=timezone.utc)
        end = start + timedelta(days=7)
        grouped = self.db.execute(
            select(
                Alert.sensor_id,
                func.date(Alert.created_at),
                func.count(Alert.id),
            )
            .join(Sensor, Sensor.id == Alert.sensor_id)
            .where(
                Sensor.site_id == site_id,
                Alert.created_at >= start,
                Alert.created_at < end,
            )
            .group_by(Alert.sensor_id, func.date(Alert.created_at))
        ).all()
        counts = {(sensor_id, str(day)): int(total) for sensor_id, day, total in grouped}
        days = [week_start + timedelta(days=i) for i in range(7)]
        return {
            "site_id": site.id,
            "site_name": site.name,
            "week_start": week_start,
            "days": days,
            "rows": [
                {
                    "sensor_id": sensor_id,
                    "sensor_name": name,
                    "floor": floor,
                    "counts": [counts.get((sensor_id, day.isoformat()), 0) for day in days],
                }
                for sensor_id, name, floor in sensors
            ],
        }

    def top_sensors(self, days: int, organization_id: UUID | None) -> list[dict]:
        start = datetime.now(timezone.utc) - timedelta(days=days)
        query = (
            select(
                Sensor.id,
                Sensor.name,
                Site.id,
                Site.name,
                Organization.name,
                func.count(Alert.id),
                func.sum(case((Alert.severity == "CRITICAL", 1), else_=0)),
                func.max(Alert.created_at),
            )
            .join(Site, Site.id == Sensor.site_id)
            .join(Organization, Organization.id == Site.organization_id)
            .join(Alert, Alert.sensor_id == Sensor.id)
            .where(Alert.created_at >= start)
            .group_by(Sensor.id, Sensor.name, Site.id, Site.name, Organization.name)
            .order_by(func.count(Alert.id).desc(), Sensor.id)
            .limit(10)
        )
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        return [
            {
                "sensor_id": sensor_id,
                "sensor_name": sensor_name,
                "site_id": site_id,
                "site_name": site_name,
                "organization_name": organization_name,
                "alert_count": int(alert_count),
                "critical_count": int(critical_count or 0),
                "last_alert_at": last_alert_at,
            }
            for sensor_id, sensor_name, site_id, site_name, organization_name,
            alert_count, critical_count, last_alert_at in self.db.execute(query).all()
        ]
