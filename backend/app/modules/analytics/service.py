# SERVICE — analytics
# Reglas de negocio y orquestación. No hablar HTTP aquí.
# KPIs, agregaciones, rangos y exportación.
"""
Exportación CSV de la analítica (issue #134, B18).

Una fila por sensor y día con lecturas o alertas en el periodo. Junta las
dos cosas en la misma tabla para que se abra tal cual en una hoja de
cálculo. Las columnas están en `EXPORT_COLUMNS` y en el README.
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.analytics.repository import AnalyticsRepository
from app.modules.analytics.schemas import EXPORT_COLUMNS
from app.shared.dependencies import DbSession

# Excel only reads a CSV as UTF-8 (accents in "Alcalá") if it starts with
# a BOM. Other tools ignore it.
UTF8_BOM = "\ufeff"


def _bar(value: Decimal | None) -> str:
    return "" if value is None else f"{value:.3f}"


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.repository = AnalyticsRepository(db)

    def export_rows(
        self, organization_id: UUID | None, start: datetime, end: datetime
    ) -> list[dict[str, str | int]]:
        readings = {
            (r.sensor_id, r.day): r
            for r in self.repository.readings_by_sensor_and_day(organization_id, start, end)
        }
        alerts = {
            (a.sensor_id, a.day): a
            for a in self.repository.alerts_by_sensor_and_day(organization_id, start, end)
        }
        keys = readings.keys() | alerts.keys()
        sensors = self.repository.sensors({sensor_id for sensor_id, _ in keys})

        rows = []
        for sensor_id, day in keys:
            sensor = sensors[sensor_id]
            reading = readings.get((sensor_id, day))
            alert = alerts.get((sensor_id, day))
            rows.append(
                {
                    "date": day,
                    "organization": sensor.organization,
                    "site": sensor.site,
                    "sensor_id": str(sensor_id),
                    "sensor_external_id": sensor.external_id,
                    "sensor_name": sensor.name,
                    "unit": sensor.unit,
                    "readings_count": reading.count if reading else 0,
                    "pressure_min": _bar(reading.minimum if reading else None),
                    "pressure_avg": _bar(reading.average if reading else None),
                    "pressure_max": _bar(reading.maximum if reading else None),
                    "alerts_total": alert.total if alert else 0,
                    "alerts_critical": alert.critical if alert else 0,
                    "alerts_resolved": alert.resolved if alert else 0,
                }
            )
        rows.sort(
            key=lambda r: (r["date"], r["organization"], r["site"], r["sensor_external_id"])
        )
        return rows

    def export_csv(
        self, organization_id: UUID | None, start: datetime, end: datetime
    ) -> str:
        buffer = io.StringIO()
        buffer.write(UTF8_BOM)
        writer = csv.DictWriter(buffer, fieldnames=EXPORT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(self.export_rows(organization_id, start, end))
        return buffer.getvalue()


def get_analytics_service(db: DbSession) -> AnalyticsService:
    """Proveedor del service para `Depends`."""
    return AnalyticsService(db)
