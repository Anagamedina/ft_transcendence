# SCHEMAS — analytics
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""Contrato de la exportación CSV (issue #134, B18)."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class ExportFormat(str, Enum):
    """
    `csv` descarga el archivo. `json` devuelve las mismas filas para que el
    panel (F19) dibuje los gráficos sin parsear CSV. El PDF queda fuera.
    """

    CSV = "csv"
    JSON = "json"


class DailyRow(BaseModel):
    """Una fila de la exportación en JSON: mismas columnas que el CSV."""

    date: str
    organization: str
    site: str
    sensor_id: UUID
    sensor_external_id: str
    sensor_name: str
    unit: str
    readings_count: int
    # null when the sensor sent no readings that day
    pressure_min: float | None
    pressure_avg: float | None
    pressure_max: float | None
    alerts_total: int
    alerts_critical: int
    alerts_resolved: int


# Columnas del CSV, en orden. Son parte del contrato con el frontend (F19):
# cambiarlas es un cambio de API. Documentadas también en el README.
#
#   date                YYYY-MM-DD, en UTC
#   organization, site  nombres actuales
#   sensor_id           UUID del sensor
#   sensor_external_id  identificador del fabricante
#   sensor_name, unit   unidad de las tres columnas de presión
#   readings_count      lecturas recibidas ese día
#   pressure_min/avg/max  presión mínima, media y máxima (3 decimales; vacías sin lecturas)
#   alerts_total        alertas creadas ese día
#   alerts_critical     de ellas, CRITICAL
#   alerts_resolved     de ellas, ya resueltas
EXPORT_COLUMNS = [
    "date",
    "organization",
    "site",
    "sensor_id",
    "sensor_external_id",
    "sensor_name",
    "unit",
    "readings_count",
    "pressure_min",
    "pressure_avg",
    "pressure_max",
    "alerts_total",
    "alerts_critical",
    "alerts_resolved",
]
