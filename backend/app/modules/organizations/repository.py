"""Persistence queries for organizations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.orm import Session

from app.modules.alerts.model import Alert
from app.modules.organizations.model import Organization
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site
from app.modules.users.model import User
from app.shared.utils import matches_text


@dataclass(frozen=True)
class OrganizationCounts:
    """Counters of an organization for `OrganizationResponse` (B1)."""

    sites: int = 0
    sensors: int = 0
    users: int = 0
    open_alerts: int = 0
    critical_alerts: int = 0
    # Creation of the oldest open alert; None if it has none.
    oldest_open_alert_at: datetime | None = None


def _has_open_alerts():
    """
    Condition "the organization has some unresolved alert".

    `EXISTS` and not a JOIN: only whether there is one matters, not how
    many, and so an organization with 50 alerts does not appear 50 times
    in the list.
    """
    return exists(
        select(Alert.id)
        .join(Sensor, Alert.sensor_id == Sensor.id)
        .join(Site, Sensor.site_id == Site.id)
        .where(Site.organization_id == Organization.id, Alert.status == "ACTIVE")
    )


def _sort_column(sort: str):
    """
    The expression `list()` sorts by for each `OrganizationSort` value.

    The counters are correlated subqueries and not a JOIN with GROUP BY:
    so the filter, the total and the pagination do not change, and they
    are only computed for the rows being sorted.
    """
    if sort == "name":
        return Organization.name
    if sort == "trial_ends_at":
        return Organization.trial_ends_at
    if sort == "site_count":
        query = select(func.count(Site.id)).where(Site.organization_id == Organization.id)
    elif sort == "sensor_count":
        query = (
            select(func.count(Sensor.id))
            .join(Site, Sensor.site_id == Site.id)
            .where(Site.organization_id == Organization.id)
        )
    elif sort == "user_count":
        query = select(func.count(User.id)).where(User.organization_id == Organization.id)
    elif sort == "open_alerts":
        query = (
            select(func.count(Alert.id))
            .join(Sensor, Alert.sensor_id == Sensor.id)
            .join(Site, Sensor.site_id == Site.id)
            .where(Site.organization_id == Organization.id, Alert.status == "ACTIVE")
        )
    else:
        raise ValueError(f"Unknown sort: {sort}")
    return query.correlate(Organization).scalar_subquery()


class OrganizationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, organization_id: UUID) -> Organization | None:
        return self.db.get(Organization, organization_id)

    # Added by Ana for B1 (#139).
    def get_for_update(self, organization_id: UUID) -> Organization | None:
        """
        The organization with its row locked (`SELECT … FOR UPDATE`) until
        the commit or rollback of the current transaction.

        It is for status changes: another request wanting to change the
        same organization waits here and, when it gets in, reads the
        already changed status. `populate_existing` fills the object with
        what the query returns even if the session already had it loaded;
        otherwise it would validate with old data. SQLite has no
        `FOR UPDATE` and ignores it.
        """
        return self.db.scalar(
            select(Organization)
            .where(Organization.id == organization_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    def list(
        self,
        offset: int = 0,
        limit: int = 100,
        q: str | None = None,
        status: str | None = None,
        has_open_alerts: bool | None = None,
        sort: str = "name",
        descending: bool = False,
    ) -> tuple[list[Organization], int]:
        """
        Organizations ordered by `sort` (see `_sort_column`). No
        organization scope: only the admin lists them, and the router
        checks that.

        `q` searches the name, the city, the legal name and the tax id.
        """
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        query = select(Organization)
        if q is not None:
            query = query.where(
                matches_text(
                    q,
                    Organization.name,
                    Organization.city,
                    Organization.legal_name,
                    Organization.tax_id,
                )
            )
        if status is not None:
            query = query.where(Organization.status == status)
        if has_open_alerts is True:
            query = query.where(_has_open_alerts())
        elif has_open_alerts is False:
            query = query.where(~_has_open_alerts())

        total = self.db.scalar(select(func.count()).select_from(query.subquery()))

        column = _sort_column(sort)
        # Those without a trial end date (active clients) go last in both
        # directions: they are not "the ones ending soonest".
        primary = (column.desc() if descending else column.asc()).nulls_last()
        items = list(
            self.db.scalars(
                # The name breaks ties, then the id, as in sites and sensors,
                # so pagination never repeats or skips an organization.
                query.order_by(primary, Organization.name, Organization.id)
                .offset(offset)
                .limit(limit)
            ).all()
        )
        return items, int(total or 0)

    def counts(self, organization_ids: list[UUID]) -> dict[UUID, OrganizationCounts]:
        """
        Counters of several organizations at once.

        One `GROUP BY` query per counter for the whole page, not one per
        organization: with 20 organizations that is 4 queries, not 80.
        Organizations with nothing do not show up in the results and keep
        the default zeros.
        """
        if not organization_ids:
            return {}

        sites = dict(
            self.db.execute(
                select(Site.organization_id, func.count(Site.id))
                .where(Site.organization_id.in_(organization_ids))
                .group_by(Site.organization_id)
            ).all()
        )
        sensors = dict(
            self.db.execute(
                select(Site.organization_id, func.count(Sensor.id))
                .join(Sensor, Sensor.site_id == Site.id)
                .where(Site.organization_id.in_(organization_ids))
                .group_by(Site.organization_id)
            ).all()
        )
        users = dict(
            self.db.execute(
                select(User.organization_id, func.count(User.id))
                .where(User.organization_id.in_(organization_ids))
                .group_by(User.organization_id)
            ).all()
        )
        open_alerts: dict[UUID, int] = {}
        critical: dict[UUID, int] = {}
        oldest: dict[UUID, datetime] = {}
        filas = self.db.execute(
            select(
                Site.organization_id,
                Alert.severity,
                func.count(Alert.id),
                func.min(Alert.created_at),
            )
            .join(Sensor, Sensor.site_id == Site.id)
            .join(Alert, Alert.sensor_id == Sensor.id)
            .where(
                Site.organization_id.in_(organization_ids),
                Alert.status == "ACTIVE",
            )
            .group_by(Site.organization_id, Alert.severity)
        ).all()
        for organization_id, severity, n, primera in filas:
            open_alerts[organization_id] = open_alerts.get(organization_id, 0) + n
            if severity == "CRITICAL":
                critical[organization_id] = n
            if organization_id not in oldest or primera < oldest[organization_id]:
                oldest[organization_id] = primera

        return {
            oid: OrganizationCounts(
                sites=sites.get(oid, 0),
                sensors=sensors.get(oid, 0),
                users=users.get(oid, 0),
                open_alerts=open_alerts.get(oid, 0),
                critical_alerts=critical.get(oid, 0),
                oldest_open_alert_at=oldest.get(oid),
            )
            for oid in organization_ids
        }

    def name_taken(self, name: str, exclude_id: UUID | None = None) -> bool:
        """
        True if another organization already uses that name, ignoring
        case: the same rule as the table's unique index
        `uq_organizations_name_lower` (#120).
        """
        query = select(Organization.id).where(
            func.lower(Organization.name) == name.lower()
        )
        if exclude_id is not None:
            query = query.where(Organization.id != exclude_id)
        return self.db.scalar(query.limit(1)) is not None

    def create(self, **campos) -> Organization:
        organization = Organization(**campos)
        self.db.add(organization)
        self.db.flush()
        return organization

    def update(self, organization: Organization, **campos) -> Organization:
        for nombre, valor in campos.items():
            setattr(organization, nombre, valor)
        self.db.flush()
        return organization
