"""Organization-scoped persistence queries for sensors."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site


class SensorRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_organization(
        self,
        organization_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Sensor], int]:
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        query = select(Sensor).join(Site).where(
            Site.organization_id == organization_id
        )

        total = self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )

        items = list(
            self.db.scalars(
                query.order_by(Sensor.id).offset(offset).limit(limit)
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
        return self.db.scalar(query)

    def get(self, sensor_id: UUID) -> Sensor | None:
        """
        Busca un sensor solo por su id, SIN filtrar por organización.

        Es la excepción de este módulo y conviene saber por qué existe. La
        usa `POST /api/readings` (issue #24): quien llama ahí es el
        simulador, que no tiene sesión y por tanto no puede aportar una
        organización. La organización se deduce después *del sensor
        encontrado*, no de quien envía.

        No sustituye a `get_by_id`: para todo lo que pida un usuario con
        sesión se sigue usando aquel, que sí aísla por organización.
        """
        return self.db.scalar(select(Sensor).where(Sensor.id == sensor_id))
