# SCHEMAS — analytics
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""Contrato de la exportación CSV (issue #134, B18) y del panel de KPIs (B9, #144)."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.shared.schemas import ApiModel


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


# ---------------------------------------------------------
# CONTRATO DE LA B9 — panel y KPIs (Ana, #144)
# ---------------------------------------------------------
# Se publica antes que las rutas, como en la #23, para que el panel (F12,
# Eduardo) se monte con mocks. Rutas previstas, todas con sesión; un
# cliente solo ve su organización (OrgScope):
#
#   GET /api/analytics/overview                               → OverviewResponse
#   GET /api/analytics/alerts/weekly?site_id=&week_start=     → WeeklyAlertsResponse
#   GET /api/analytics/alerts/top-sensors?days=30             → TopSensorsResponse


class OverviewResponse(ApiModel):
    """
    Las tarjetas de KPI del panel. Los dos campos de organizaciones solo
    tienen valor para el admin; para un cliente salen `null`.
    """

    organizations_total: int | None = Field(
        default=None, description="Clientes (solo admin).", examples=[5]
    )
    organizations_needing_attention: int | None = Field(
        default=None,
        description="Clientes con alguna alerta sin resolver (solo admin).",
        examples=[2],
    )
    sites_total: int = Field(examples=[6])
    sensors_total: int = Field(examples=[8])
    sensors_online: int = Field(
        description="Sensores que han mandado una lectura en los últimos 5 minutos.",
        examples=[6],
    )
    open_alerts: int = Field(description="Alertas sin resolver.", examples=[3])
    critical_open_alerts: int = Field(
        description="De ellas, CRITICAL.", examples=[1]
    )
    median_resolution_minutes: float | None = Field(
        default=None,
        description=(
            "Mediana de lo que tardaron en resolverse las alertas resueltas "
            "en los últimos 30 días (`percentile_cont` de PostgreSQL). Nula "
            "si no se resolvió ninguna."
        ),
        examples=[42.5],
    )


class WeeklyAlertsRow(ApiModel):
    """Una fila del mapa de calor: un sensor y sus alertas de cada día."""

    sensor_id: UUID
    sensor_name: str = Field(examples=["Presión entrada"])
    floor: int = Field(examples=[0])
    counts: list[int] = Field(
        description="Alertas creadas cada día, en el orden de `days` (7 números).",
        examples=[[0, 2, 0, 1, 0, 0, 3]],
    )


class WeeklyAlertsResponse(ApiModel):
    """Alertas de una semana por sensor y día, de un edificio."""

    site_id: UUID
    site_name: str = Field(examples=["Residencia Sant Gervasi"])
    week_start: date = Field(
        description="Lunes de la semana. Por defecto, el de la semana actual.",
        examples=["2026-10-05"],
    )
    days: list[date] = Field(
        description="Los 7 días de la semana, de lunes a domingo, en UTC.",
    )
    rows: list[WeeklyAlertsRow] = Field(
        description="Un sensor por fila, también los que no tuvieron alertas."
    )


class TopSensorItem(ApiModel):
    """Un sensor del ranking de los que más alertas dan."""

    sensor_id: UUID
    sensor_name: str = Field(examples=["Presión vestuarios"])
    site_id: UUID
    site_name: str = Field(examples=["Polideportivo Poblenou"])
    organization_name: str = Field(examples=["Polideportivo Poblenou"])
    alert_count: int = Field(examples=[12])
    critical_count: int = Field(examples=[4])
    last_alert_at: datetime | None = None


class TopSensorsResponse(ApiModel):
    """Los sensores con más alertas en los últimos `days` días (30 por defecto)."""

    days: int = Field(examples=[30])
    items: list[TopSensorItem] = Field(
        description="De más a menos alertas; como mucho 10."
    )
