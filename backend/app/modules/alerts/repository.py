# REPOSITORY — alerts
# Data access (SQLAlchemy queries). Always filter by organization.
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from app.modules.alerts.model import Alert
from app.modules.organizations.model import Organization
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.shared.utils import matches_text


def _con_lectura():
    """Location and actors in bulk, also when each row has different users."""
    return (
        _con_jerarquia(),
        selectinload(Alert.acknowledged_by_user),
        selectinload(Alert.resolved_by_user),
        selectinload(Alert.notifications),
    )


def _con_jerarquia():
    """
    What `AlertService._to_response` needs for the read-only fields (B0):
    the sensor, its site and the site's organization.

    `selectinload` and not `joinedload` because the queries already do
    `join(Sensor).join(Site)` to filter; this way the JOINs are not
    duplicated and each level is loaded with a single query for the whole
    page. It is a function and not a constant: building the option
    configures the mappers, and when this module is imported not every
    model is registered yet.
    """
    return (
        selectinload(Alert.sensor)
        .selectinload(Sensor.site)
        .selectinload(Site.organization)
    )


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
            organization_id: UUID | None,
            *,
            for_update: bool = False,
    ) -> Alert | None:
        # #27 (Ana): organization_id=None means ALL organizations (admin).
        # `get_org_scope` in shared/dependencies.py decides it.
        query = (
            select(Alert).join(Sensor).join(Site)
            .where(Alert.id == alert_id)
        )
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        if for_update:
            # Only the alert: do not lock sensor/site nor use stale values
            # from the identity map after waiting for another operator.
            query = query.with_for_update(of=Alert).execution_options(
                populate_existing=True,
            )
        return self.db.scalar(query.options(*_con_lectura()))

    def list_by_organization(
            self, organization_id: UUID | None, status: str | None = None,
            sensor_id: UUID | None = None,
            offset: int = 0, limit: int = 100,
            q: str | None = None,
            organization_filter: UUID | None = None,
            site_id: UUID | None = None,
            severity: str | None = None,
            state: str | None = None,
            created_from: datetime | None = None,
            created_to: datetime | None = None,
    ) -> tuple[list[Alert], int]:
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        # #27 (Ana): organization_id=None means ALL organizations (admin).
        # `get_org_scope` in shared/dependencies.py decides it.
        query = select(Alert).join(Sensor).join(Site)
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        if status is not None:
            query = query.where(Alert.status == status)
        if sensor_id is not None:
            query = query.where(Alert.sensor_id == sensor_id)
        # B0 (Ana): common filters. They add to the scope, they do not replace it.
        if organization_filter is not None:
            query = query.where(Site.organization_id == organization_filter)
        if site_id is not None:
            query = query.where(Sensor.site_id == site_id)
        if q is not None:
            # #252: also by sensor code, building and client
            # ("Buscar sensor, edificio o cliente" on the admin page).
            clientes = select(Organization.id).where(matches_text(q, Organization.name))
            query = query.where(
                matches_text(q, Alert.message, Sensor.name, Sensor.external_id, Site.name)
                | Site.organization_id.in_(clientes)
            )
        if severity is not None:
            query = query.where(Alert.severity == severity)
        if state == "RESOLVED":
            query = query.where(Alert.status == "RESOLVED")
        elif state == "ACKNOWLEDGED":
            query = query.where(
                Alert.status == "ACTIVE", Alert.acknowledged_at.is_not(None),
            )
        elif state == "ACTIVE":
            query = query.where(Alert.status == "ACTIVE", Alert.acknowledged_at.is_(None))
        if created_from is not None:
            query = query.where(Alert.created_at >= created_from)
        if created_to is not None:
            query = query.where(Alert.created_at < created_to)

        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = list(self.db.scalars(
            query.options(*_con_lectura())
            .order_by(Alert.created_at.desc(), Alert.id.desc()).offset(offset).limit(limit)
        ).all())
        return items, int(total or 0)

    def acknowledge(
        self, alert_id: UUID, when: datetime, actor_id: UUID | None = None,
    ) -> Alert | None:
        """The service locks the row before writing date and actor together."""
        alert = self.db.get(Alert, alert_id)
        if alert is None:
            return None
        if alert.acknowledged_at is None:
            alert.acknowledged_at = when
            alert.acknowledged_by = actor_id
            self.db.expire(alert, ["acknowledged_by_user"])
        return alert

    def resolve(
        self, alert_id: UUID, when: datetime, actor_id: UUID | None = None,
    ) -> Alert | None:
        """The service checks the state with the row locked before closing."""
        alert = self.db.get(Alert, alert_id)
        if alert is None:
            return None
        alert.status = "RESOLVED"
        alert.resolved_at = when
        alert.resolved_by = actor_id
        self.db.expire(alert, ["resolved_by_user"])
        return alert

    # Added by Ana for the #28 rules. No organization filter on purpose:
    # `ReadingService.create()` calls them, receiving readings from the
    # simulator, without a session, after checking that the sensor exists.
    def get_active(self, sensor_id: UUID, alert_type: str) -> Alert | None:
        # The newest one, in case two were already open: nothing in the
        # table prevents it yet.
        query = (
            select(Alert)
            .where(
                Alert.sensor_id == sensor_id,
                Alert.alert_type == alert_type,
                Alert.status == "ACTIVE",
            )
            .order_by(Alert.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(query)

    def escalate(self, alert: Alert, severity: str, message: str) -> Alert:
        alert.severity = severity
        alert.message = message
        self.db.flush()
        return alert
