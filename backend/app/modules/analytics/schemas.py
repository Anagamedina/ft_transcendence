# SCHEMAS — analytics
# Pydantic request/response (OpenAPI contract). Never return a raw ORM model.
"""Contract of the CSV export (issue #134, B18) and of the KPI panel (B9, #144)."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

from app.shared.schemas import ApiModel


class ExportFormat(str, Enum):
    """
    `csv` downloads the file. `json` returns the same rows so the panel
    (F19) draws the charts without parsing CSV. PDF is out of scope.
    """

    CSV = "csv"
    JSON = "json"


class DailyRow(BaseModel):
    """One row of the export in JSON: the same columns as the CSV."""

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


# CSV columns, in order. They are part of the contract with the frontend
# (F19): changing them is an API change. Also documented in the README.
#
#   date                YYYY-MM-DD, in UTC
#   organization, site  current names
#   sensor_id           sensor UUID
#   sensor_external_id  manufacturer identifier
#   sensor_name, unit   unit of the three pressure columns
#   readings_count      readings received that day
#   pressure_min/avg/max  minimum, average and maximum pressure (3 decimals; empty without readings)
#   alerts_total        alerts created that day
#   alerts_critical     of them, CRITICAL
#   alerts_resolved     of them, already resolved
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
# B9 CONTRACT — panel and KPIs (Ana, #144)
# ---------------------------------------------------------
# Published before the routes, as in #23, so the panel (F12, Eduardo)
# could be built with mocks. Routes, all with a session; a client only
# sees its organization (OrgScope):
#
#   GET /api/analytics/overview                               → OverviewResponse
#   GET /api/analytics/alerts/weekly?site_id=&week_start=     → WeeklyAlertsResponse
#   GET /api/analytics/alerts/top-sensors?days=30             → TopSensorsResponse


class OverviewResponse(ApiModel):
    """
    The KPI cards of the panel. The two organization fields only have a
    value for the admin; for a client they are `null`.
    """

    organizations_total: int | None = Field(
        default=None, description="Clients (admin only).", examples=[5]
    )
    organizations_needing_attention: int | None = Field(
        default=None,
        description="Clients with some unresolved alert (admin only).",
        examples=[2],
    )
    sites_total: int = Field(examples=[6])
    sensors_total: int = Field(examples=[8])
    sensors_online: int = Field(
        description="Sensors that sent a reading in the last 5 minutes.",
        examples=[6],
    )
    open_alerts: int = Field(description="Unresolved alerts.", examples=[3])
    critical_open_alerts: int = Field(
        description="Of them, CRITICAL.", examples=[1]
    )
    median_resolution_minutes: float | None = Field(
        default=None,
        description=(
            "Median time to resolve the alerts resolved in the last 30 days "
            "(PostgreSQL `percentile_cont`). Null if none was resolved."
        ),
        examples=[42.5],
    )


class WeeklyAlertsRow(ApiModel):
    """One row of the heat map: a sensor and its alerts on each day."""

    sensor_id: UUID
    sensor_name: str = Field(examples=["Presión entrada"])
    floor: int = Field(examples=[0])
    counts: list[int] = Field(
        description="Alerts created each day, in the order of `days` (7 numbers).",
        examples=[[0, 2, 0, 1, 0, 0, 3]],
    )


class WeeklyAlertsResponse(ApiModel):
    """Alerts of one week per sensor and day, of one building."""

    site_id: UUID
    site_name: str = Field(examples=["Residencia Sant Gervasi"])
    week_start: date = Field(
        description="Monday of the week. By default, the current week's.",
        examples=["2026-10-05"],
    )
    days: list[date] = Field(
        description="The 7 days of the week, Monday to Sunday, in UTC.",
    )
    rows: list[WeeklyAlertsRow] = Field(
        description="One sensor per row, also those without alerts."
    )


class TopSensorItem(ApiModel):
    """A sensor of the ranking of those with the most alerts."""

    sensor_id: UUID
    sensor_name: str = Field(examples=["Presión vestuarios"])
    site_id: UUID
    site_name: str = Field(examples=["Polideportivo Poblenou"])
    organization_name: str = Field(examples=["Polideportivo Poblenou"])
    alert_count: int = Field(examples=[12])
    critical_count: int = Field(examples=[4])
    last_alert_at: datetime | None = None


class TopSensorsResponse(ApiModel):
    """The sensors with the most alerts in the last `days` days (30 by default)."""

    days: int = Field(examples=[30])
    items: list[TopSensorItem] = Field(
        description="From most to fewest alerts; 10 at most."
    )
