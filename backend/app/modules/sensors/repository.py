"""Organization-scoped persistence queries for sensors."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.readings.model import Reading
from app.modules.sensors.model import Sensor
from app.modules.sites.model import Site


class SensorRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_by_organization(
        self,
        organization_id: UUID | None,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Sensor], int]:
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        # #27 (Ana): organization_id=None significa TODAS las organizaciones
        # (admin). Lo decide `get_org_scope` en shared/dependencies.py.
        query = select(Sensor).join(Site)
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)

        total = self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )

        items = list(
            self.db.scalars(
                # #25 (Ana): por nombre, como los sites; el id desempata para
                # que la paginación no repita ni salte sensores.
                query.order_by(Sensor.name, Sensor.id).offset(offset).limit(limit)
            ).all()
        )

        return items, int(total or 0)

    def get_by_id(
        self,
        sensor_id: UUID,
        organization_id: UUID | None,
    ) -> Sensor | None:
        # #27 (Ana): organization_id=None significa TODAS las organizaciones
        # (admin). Lo decide `get_org_scope` en shared/dependencies.py.
        query = select(Sensor).join(Site).where(Sensor.id == sensor_id)
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        return self.db.scalar(query)

    def last_seen_by_sensor(self, sensor_ids: list[UUID]) -> dict[UUID, datetime]:
        """
        Cuándo llegó la última lectura de cada sensor (#25, Ana).

        Una sola consulta para toda la página, no una por sensor. Los
        sensores sin lecturas no aparecen en el diccionario.

        Usa `created_at` (cuándo la recibió el backend) y no `recorded_at`
        (cuándo dice el sensor que la midió); ver `sensors/status.py`. Hoy
        no hay índice por `(sensor_id, created_at)`: con muchas lecturas
        convendrá crearlo.
        """
        if not sensor_ids:
            return {}
        filas = self.db.execute(
            select(Reading.sensor_id, func.max(Reading.created_at))
            .where(Reading.sensor_id.in_(sensor_ids))
            .group_by(Reading.sensor_id)
        ).all()
        return {sensor_id: ultima for sensor_id, ultima in filas}

    # Añadidos por Ana para la #29 (partes B y C).
    def list_by_site(
        self, site_id: UUID, offset: int = 0, limit: int = 100
    ) -> tuple[list[Sensor], int]:
        """
        Sensores de un site, por nombre. No filtra por organización: quien
        llama ya ha comprobado que el site es visible para el usuario.
        """
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")
        query = select(Sensor).where(Sensor.site_id == site_id)
        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = list(
            self.db.scalars(
                query.order_by(Sensor.name, Sensor.id).offset(offset).limit(limit)
            ).all()
        )
        return items, int(total or 0)

    def external_id_taken(self, site_id: UUID, external_id: str) -> bool:
        """True si ya hay un sensor con esa etiqueta en ese site."""
        return (
            self.db.scalar(
                select(Sensor.id).where(
                    Sensor.site_id == site_id, Sensor.external_id == external_id
                )
            )
            is not None
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
