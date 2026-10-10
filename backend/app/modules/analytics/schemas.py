# SCHEMAS — analytics
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""Contrato de la exportación CSV (issue #134, B18)."""

from __future__ import annotations

from enum import Enum


class ExportFormat(str, Enum):
    """Solo CSV: el PDF es opcional y queda fuera de la B18."""

    CSV = "csv"


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
