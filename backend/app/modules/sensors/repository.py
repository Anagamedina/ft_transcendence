"""Organization-scoped persistence queries for sensors."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import and_, exists, func, not_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.modules.alerts.model import Alert
from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sensors.status import OFFLINE_TRAS
from app.modules.sites.model import Site
from app.shared.enums import AlertSeverity, AlertStatus, SensorHealth
from app.shared.utils import matches_text


@dataclass(frozen=True)
class SensorLive:
    """
    What is known about a sensor from its readings and alerts (B3): the
    basis of `status`, `last_seen_at`, `last_value` and `health` in
    `SensorResponse`. Without readings or alerts, everything empty.
    """

    last_seen_at: datetime | None = None
    last_value: Decimal | None = None
    open_severities: frozenset[str] = frozenset()


def _filtro_salud(salud: SensorHealth, ahora: datetime):
    """
    `?health=` in SQL (B3). It is the `calcular_salud` rule
    (`sensors/status.py`) written as a condition, so the filter applies
    before paginating and `total` only counts the matching ones.
    """
    ultima = (
        select(func.max(Reading.created_at))
        .where(Reading.sensor_id == Sensor.id)
        .scalar_subquery()
    )
    offline = or_(ultima.is_(None), ultima < ahora - OFFLINE_TRAS)

    def con_alerta(severidad: AlertSeverity):
        return exists(
            select(Alert.id).where(
                Alert.sensor_id == Sensor.id,
                Alert.status == AlertStatus.ACTIVE.value,
                Alert.severity == severidad.value,
            )
        )

    critica = con_alerta(AlertSeverity.CRITICAL)
    aviso = con_alerta(AlertSeverity.WARNING)
    return {
        SensorHealth.OFFLINE: offline,
        SensorHealth.CRITICAL: and_(not_(offline), critica),
        SensorHealth.WARNING: and_(not_(offline), not_(critica), aviso),
        SensorHealth.OK: and_(not_(offline), not_(critica), not_(aviso)),
    }[salud]


def _con_jerarquia():
    """
    Site and organization of each sensor, for the read-only fields of
    `SensorResponse` (B0). One query per level for the whole page.

    It is a function and not a constant: building the option configures
    the mappers, and when this module is imported not every model is
    registered yet (`Reading`).
    """
    return selectinload(Sensor.site).selectinload(Site.organization)


class SensorRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_organization(
        self,
        organization_id: UUID | None,
        offset: int = 0,
        limit: int = 100,
        q: str | None = None,
        organization_filter: UUID | None = None,
        site_id: UUID | None = None,
        health: SensorHealth | None = None,
        ahora: datetime | None = None,
    ) -> tuple[list[Sensor], int]:
        """
        `health` (B3) needs `ahora` ("now"), the same instant the service
        uses to compute the health of the response.
        """
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")
        if health is not None and ahora is None:
            raise ValueError("health necesita ahora")

        # #27 (Ana): organization_id=None means ALL organizations (admin).
        # `get_org_scope` in shared/dependencies.py decides it.
        query = select(Sensor).join(Site)
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        # B0 (Ana): common filters. They add to the scope, they do not replace it.
        if organization_filter is not None:
            query = query.where(Site.organization_id == organization_filter)
        if site_id is not None:
            query = query.where(Sensor.site_id == site_id)
        if q is not None:
            query = query.where(
                matches_text(q, Sensor.name, Sensor.external_id, Sensor.location)
            )
        if health is not None:
            query = query.where(_filtro_salud(health, ahora))

        total = self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )

        items = list(
            self.db.scalars(
                # #25 (Ana): by name, like sites; the id breaks ties so
                # pagination never repeats or skips sensors.
                query.options(_con_jerarquia())
                .order_by(Sensor.name, Sensor.id).offset(offset).limit(limit)
            ).all()
        )

        return items, int(total or 0)

    def get_by_id(
        self,
        sensor_id: UUID,
        organization_id: UUID | None,
    ) -> Sensor | None:
        # #27 (Ana): organization_id=None means ALL organizations (admin).
        # `get_org_scope` in shared/dependencies.py decides it.
        query = select(Sensor).join(Site).where(Sensor.id == sensor_id)
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        return self.db.scalar(query.options(_con_jerarquia()))

    # Added by Ana for B3 (#139).
    def live(self, sensor_ids: list[UUID]) -> dict[UUID, SensorLive]:
        """
        Last reading and open alerts of several sensors: two queries for
        the whole page, not two per sensor.

        The last reading is the last one that **arrived** (`created_at`),
        the same one behind `last_seen_at`; so `last_value` and
        `last_seen_at` always talk about the same reading. Open alerts are
        the `ACTIVE` ones, acknowledged or not.
        """
        if not sensor_ids:
            return {}

        # D5: for each sensor of the page, the id of its last reading with
        # ORDER BY ... LIMIT 1, which PostgreSQL resolves by reading only
        # the last entry of ix_readings_sensor_created_at; then the reading
        # by its key. The former row_number() numbered every reading of
        # each sensor before keeping the first.
        ultima = (
            select(Reading.id)
            .where(Reading.sensor_id == Sensor.id)
            .order_by(Reading.created_at.desc(), Reading.id.desc())
            .limit(1)
            .correlate(Sensor)
            .scalar_subquery()
        )
        lecturas = {
            sensor_id: (cuando, valor)
            for sensor_id, cuando, valor in self.db.execute(
                select(Sensor.id, Reading.created_at, Reading.value)
                .join(Reading, Reading.id == ultima)
                .where(Sensor.id.in_(sensor_ids))
            ).all()
        }

        severidades: dict[UUID, set[str]] = {}
        for sensor_id, severidad in self.db.execute(
            select(Alert.sensor_id, Alert.severity)
            .where(
                Alert.sensor_id.in_(sensor_ids),
                Alert.status == AlertStatus.ACTIVE.value,
            )
            .group_by(Alert.sensor_id, Alert.severity)
        ).all():
            severidades.setdefault(sensor_id, set()).add(severidad)

        return {
            sid: SensorLive(
                last_seen_at=lecturas.get(sid, (None, None))[0],
                last_value=lecturas.get(sid, (None, None))[1],
                open_severities=frozenset(severidades.get(sid, ())),
            )
            for sid in sensor_ids
        }

    def get_for_update(self, sensor_id: UUID) -> Sensor | None:
        """
        The sensor with its row locked until the end of the transaction
        (B3). To edit it: two PATCH at once go one after the other, and the
        second compares its thresholds with those the first left.

        It only locks the sensor: `selectinload` brings the site and the
        organization in separate queries, without a lock. Whoever changes
        the floor locks the site separately.
        """
        return self.db.scalar(
            select(Sensor)
            .where(Sensor.id == sensor_id)
            .options(_con_jerarquia())
            .with_for_update()
            .execution_options(populate_existing=True)
        )

    # Added by Ana for #29 (parts B and C).
    def list_by_site(
        self, site_id: UUID, offset: int = 0, limit: int = 100
    ) -> tuple[list[Sensor], int]:
        """
        Sensors of a site, by name. It does not filter by organization: the
        caller has already checked that the site is visible to the user.
        """
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")
        query = select(Sensor).where(Sensor.site_id == site_id)
        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = list(
            self.db.scalars(
                query.options(_con_jerarquia())
                .order_by(Sensor.name, Sensor.id).offset(offset).limit(limit)
            ).all()
        )
        return items, int(total or 0)

    def count_by_organization(self, organization_id: UUID) -> int:
        """Sensors of every building of an organization (B14 limit)."""
        return self.db.scalar(
            select(func.count())
            .select_from(Sensor)
            .join(Site, Site.id == Sensor.site_id)
            .where(Site.organization_id == organization_id)
        )

    def external_id_taken(self, site_id: UUID, external_id: str) -> bool:
        """True if that site already has a sensor with that label."""
        return (
            self.db.scalar(
                select(Sensor.id).where(
                    Sensor.site_id == site_id, Sensor.external_id == external_id
                )
            )
            is not None
        )

    def external_ids_in_site(self, site_id: UUID) -> set[str]:
        """
        The labels already used in that site. One query for the whole
        import file, not one per row.
        """
        return set(
            self.db.scalars(select(Sensor.external_id).where(Sensor.site_id == site_id))
        )

    def create(self, **campos) -> Sensor:
        sensor = Sensor(**campos)
        self.db.add(sensor)
        self.db.flush()
        return sensor

    def update(self, sensor: Sensor, **campos) -> Sensor:
        for nombre, valor in campos.items():
            setattr(sensor, nombre, valor)
        self.db.flush()
        return sensor

    def get(self, sensor_id: UUID) -> Sensor | None:
        """
        Looks a sensor up by its id alone, WITHOUT filtering by
        organization.

        It is the exception of this module and worth knowing why it exists.
        `POST /api/readings` (issue #24) uses it: the caller there is the
        simulator, which has no session and so cannot give an
        organization. The organization is derived afterwards *from the
        sensor found*, not from the sender.

        It does not replace `get_by_id`: everything a user with a session
        asks for still uses that one, which does isolate by organization.
        """
        return self.db.scalar(select(Sensor).where(Sensor.id == sensor_id))
