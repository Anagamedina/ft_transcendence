# REPOSITORY — sensors
# Acceso a datos (SQLAlchemy queries). Filtrar siempre por organización.
"""
Implements organization-scoped sensor queries, including sensor listing,
pagination, and secure lookup by sensor ID.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site


class SensorRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def list_by_organization(
        self,
        organization_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Sensor], int]:
        if offset < 0 or limit <= 0:
            raise ValueError("Paginación inválida")

        query = select(Sensor).join(Site).where(
            Site.organization_id == organization_id
        )

        total = self._db.scalar(
            select(func.count()).select_from(query.subquery())
        )

        items = list(
            self._db.scalars(
                query.order_by(Sensor.id)
                .offset(offset)
                .limit(limit)
            ).all()
        )

        return items, int(total or 0)

    def get_by_id(
        self,
        sensor_id: UUID,
        organization_id: UUID,
    ) -> Sensor | None:
        query = (
            select(Sensor)
            .join(Site)
            .where(
                Sensor.id == sensor_id,
                Site.organization_id == organization_id,
            )
        )
        return self._db.scalar(query)
