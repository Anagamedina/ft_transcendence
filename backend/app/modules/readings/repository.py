"""Organization-scoped persistence queries for readings and history."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Integer, cast, func, select
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
        id: UUID | None = None,
    ) -> Reading:
        reading = Reading(
            **({"id": id} if id is not None else {}),
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

    def get(self, reading_id: UUID) -> Reading | None:
        return self.db.get(Reading, reading_id)

    def list_by_sensor(
        self,
        sensor_id: UUID,
        organization_id: UUID | None,
        offset: int = 0,
        limit: int = 100,
        start: datetime | None = None,
        end: datetime | None = None,
        newest_first: bool = False,
    ) -> tuple[list[Reading], int]:
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        # #27 (Ana): organization_id=None significa TODAS las organizaciones
        # (admin). Lo decide `get_org_scope` en shared/dependencies.py.
        query = (
            select(Reading)
            .join(Sensor, Reading.sensor_id == Sensor.id)
            .join(Site, Sensor.site_id == Site.id)
            .where(Reading.sensor_id == sensor_id)
        )
        if organization_id is not None:
            query = query.where(Site.organization_id == organization_id)
        # B7: rango semiabierto [start, end) sobre la fecha de medida.
        if start is not None:
            query = query.where(Reading.recorded_at >= start)
        if end is not None:
            query = query.where(Reading.recorded_at < end)
        total = self.db.scalar(
            select(func.count()).select_from(query.subquery())
        )

        orden = (Reading.recorded_at, Reading.created_at, Reading.id)
        if newest_first:
            orden = tuple(columna.desc() for columna in orden)
        items = list(
            self.db.scalars(
                query.order_by(*orden)
                .offset(offset)
                .limit(limit)
            ).all()
        )

        return items, int(total or 0)

    def series_by_sensor(
        self,
        sensor_id: UUID,
        start: datetime,
        end: datetime,
        bucket: timedelta,
    ) -> list[tuple[datetime, Decimal, Decimal, Decimal]]:
        """
        B7: lecturas de un sensor en [start, end) agrupadas en tramos de
        `bucket`, con la media, el mínimo y el máximo de cada uno. Solo
        salen los tramos con lecturas, del más antiguo al más reciente.

        Los tramos se alinean a `SERIES_ORIGIN` (UTC), así que dos peticiones
        seguidas agrupan igual. No filtra por organización: el service
        comprueba antes que el sensor sea de quien pregunta.
        """
        segundos = int(bucket.total_seconds())
        if self.db.get_bind().dialect.name == "postgresql":
            tramo = func.date_bin(bucket, Reading.recorded_at, SERIES_ORIGIN)
        else:
            # sqlite (tests) no tiene date_bin: número de tramo desde el origen.
            tramo = (
                cast(func.strftime("%s", Reading.recorded_at), Integer)
                - int(SERIES_ORIGIN.timestamp())
            ) // segundos
        tramo = tramo.label("tramo")
        filas = self.db.execute(
            select(
                tramo,
                func.avg(Reading.value),
                func.min(Reading.value),
                func.max(Reading.value),
            )
            .where(
                Reading.sensor_id == sensor_id,
                Reading.recorded_at >= start,
                Reading.recorded_at < end,
            )
            .group_by(tramo)
            .order_by(tramo)
        ).all()
        return [
            (_inicio_del_tramo(t, segundos), Decimal(av), Decimal(mn), Decimal(mx))
            for t, av, mn, mx in filas
        ]


# Origen de los tramos de la serie: date_bin cuenta los tramos desde aquí.
SERIES_ORIGIN = datetime(2000, 1, 1, tzinfo=timezone.utc)


def _inicio_del_tramo(tramo: datetime | int, segundos: int) -> datetime:
    """El inicio del tramo en UTC: date_bin lo da hecho; sqlite, su número."""
    if isinstance(tramo, datetime):
        return tramo if tramo.tzinfo else tramo.replace(tzinfo=timezone.utc)
    return SERIES_ORIGIN + timedelta(seconds=int(tramo) * segundos)
