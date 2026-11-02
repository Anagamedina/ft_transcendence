# SCHEMAS — sensors
# Pydantic request/response (OpenAPI contract). Never return a raw ORM model.
"""
Sensors contract (issue #23).

Fields according to the domain model of the architecture document
(section 5):

    sensors: id, site_id, name, location, sensor_type,
             min_pressure, max_pressure, status, last_seen_at, created_at

Two things worth understanding about this module:

**The thresholds live on the sensor, not on the alert rule.** Each sensor
has its own `min_pressure` and `max_pressure` because the normal pressure
of a tank is not that of a 12th floor. Issue #28 compares each reading
with the thresholds of *its* sensor to decide whether there is
LOW_PRESSURE or HIGH_PRESSURE.

**`last_seen_at` is the basis of the third alert.** SENSOR_OFFLINE is not
detected from what arrives, but from what stops arriving: if
`last_seen_at` gets too far from now, the sensor is silent. It is not a
column: it is computed from the readings when answering
(`sensors/status.py`).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator, model_validator

# SensorType and SensorStatus live in shared/enums.py (B0); they are
# re-exported from here because the rest of the code already imports them
# from this module.
from app.shared.enums import SensorHealth, SensorStatus, SensorType
from app.shared.schemas import ApiModel, ApiRequest

# Physical limit of the measuring range we accept for an indoor
# installation pressure sensor, in bar. The real service pressure of a
# building is around 1–6 bar; the margin up to 25 covers peaks and water
# hammer without accepting an absurd reading like 900.
#
# The `sensors` table applies the same range to the thresholds with the
# `ck_sensors_threshold_range` CHECK (issue #97): if it changes here,
# change it there too with a migration.
PRESSURE_MIN_BAR = 0.0
PRESSURE_MAX_BAR = 25.0


class SensorBase(ApiRequest):
    name: str = Field(
        min_length=1,
        max_length=120,
        description="Sensor name.",
        examples=["Sensor cocina"],
    )
    location: str | None = Field(
        default=None,
        max_length=120,
        description="Area of the building where it is installed.",
        examples=["Planta 1 - Cocina"],
    )
    sensor_type: SensorType = Field(
        default=SensorType.PRESSURE,
        description="Measured quantity.",
    )
    min_pressure: float = Field(
        ge=PRESSURE_MIN_BAR,
        le=PRESSURE_MAX_BAR,
        description="Lower threshold in bar. Below it, LOW_PRESSURE is raised.",
        examples=[1.5],
    )
    max_pressure: float = Field(
        ge=PRESSURE_MIN_BAR,
        le=PRESSURE_MAX_BAR,
        description="Upper threshold in bar. Above it, HIGH_PRESSURE is raised.",
        examples=[6.0],
    )

    @field_validator("name")
    @classmethod
    def _nombre_no_vacio(cls, valor: str) -> str:
        """
        `min_length=1` does not trim: `"   "` would pass it. The spaces at
        both ends are removed and, if nothing is left, it is rejected (#29).
        """
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío.")
        return valor

    @model_validator(mode="after")
    def _check_threshold_order(self) -> "SensorBase":
        """
        Cross-field validation: the minimum must be lower than the maximum.

        `Field(ge=..., le=...)` can only look at one field at a time, so
        `min_pressure=8` with `max_pressure=2` would pass that layer. A
        `model_validator(mode="after")` runs once the object is built and
        can compare both.

        Without this the sensor would be in an impossible state: every
        reading would be too low and too high at the same time.
        """
        if self.min_pressure >= self.max_pressure:
            raise ValueError("min_pressure debe ser menor que max_pressure")
        return self


class SensorCreate(SensorBase):
    """
    Sensor creation (`POST /api/sensors`, issue #29).

    `site_id` is sent here, unlike `organization_id` in sites: the admin
    chooses the building the sensor is installed in. Only an admin can
    create sensors, and an admin sees every organization (#27), so the
    service only checks that the site exists (404 if not).
    """

    site_id: UUID = Field(description="Site where the sensor is installed.")
    external_id: str = Field(
        min_length=1,
        max_length=100,
        description=(
            "Label of the physical device or the manufacturer, different "
            "from the internal id. Unique within its site: repeating it "
            "gives 409."
        ),
        examples=["SENS-001"],
    )
    unit: str = Field(
        default="bar",
        min_length=1,
        max_length=20,
        description="Unit of measure. If not sent, `bar`.",
        examples=["bar"],
    )
    floor: int = Field(
        default=0,
        description=(
            "Floor where it is installed (B3). 0 is the ground floor; "
            "negative, a basement. It must exist in the building: between "
            "`-basements` and `floors - 1`, or 422 `FLOOR_OUT_OF_SITE`."
        ),
        examples=[2],
    )


class SensorUpdate(ApiRequest):
    """
    Partial update (`PATCH /api/sensors/{id}`, issue #29).

    It does not include `status`, `health`, `last_seen_at` or
    `last_value`: the backend computes them from the readings and the
    alerts. If the client could write them, it could mark ONLINE a sensor
    that has been silent for days.
    """

    name: str | None = Field(default=None, min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    min_pressure: float | None = Field(
        default=None, ge=PRESSURE_MIN_BAR, le=PRESSURE_MAX_BAR
    )
    max_pressure: float | None = Field(
        default=None, ge=PRESSURE_MIN_BAR, le=PRESSURE_MAX_BAR
    )
    floor: int | None = Field(
        default=None,
        description=(
            "Move the sensor to another floor (B3). Same rule as on "
            "creation: between `-basements` and `floors - 1` of its "
            "building."
        ),
    )

    @field_validator("name")
    @classmethod
    def _nombre_no_vacio(cls, valor: str | None) -> str | None:
        """Same as on creation. The service handles `None` (it cannot be cleared)."""
        if valor is None:
            return None
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío.")
        return valor

    @model_validator(mode="after")
    def _check_threshold_order(self) -> "SensorUpdate":
        """
        Here it can only compare if both thresholds arrive together.

        If the PATCH only brings `max_pressure`, it has to be checked
        against the `min_pressure` already stored, and that needs reading
        the sensor: it is a business check and the service does it, not
        the schema.
        """
        if self.min_pressure is not None and self.max_pressure is not None:
            if self.min_pressure >= self.max_pressure:
                raise ValueError("min_pressure debe ser menor que max_pressure")
        return self


class SensorResponse(ApiModel):
    id: UUID
    site_id: UUID
    # Read-only fields (B0): so lists can show the building and the client
    # without asking for them separately.
    site_name: str = Field(description="Building name.")
    organization_id: UUID = Field(description="Organization of the building.")
    organization_name: str = Field(description="Organization name.")
    floor: int = Field(
        description="Floor of the sensor. 0 is the ground floor; negative, a basement."
    )
    external_id: str = Field(
        description="Label of the physical device (`SENS-001`), unique in its site."
    )
    name: str
    location: str | None = None
    sensor_type: SensorType
    unit: str = Field(description="Unit of the readings and the thresholds.")
    min_pressure: float = Field(description="Lower threshold in bar.")
    max_pressure: float = Field(description="Upper threshold in bar.")
    status: SensorStatus = Field(description="Computed operational status.")
    health: SensorHealth = Field(
        description=(
            "Computed health (B3): `OFFLINE` if it has gone more than 5 "
            "minutes without readings; otherwise `CRITICAL` or `WARNING` "
            "depending on its unresolved alerts, and `OK` if it has none."
        )
    )
    last_seen_at: datetime | None = Field(
        default=None,
        description=(
            "Last time a reading from this sensor was received, in UTC. "
            "Null if it has never sent one."
        ),
    )
    last_value: float | None = Field(
        default=None,
        description=(
            "Value of that same last reading, in `unit` (B3). Null if it "
            "has never sent one."
        ),
        examples=[3.4],
    )
    created_at: datetime


class SensorImportRow(ApiModel):
    """A sensor of the CSV, as it will be created (or was created)."""

    line: int = Field(description="Line of the file; the header is line 1.")
    external_id: str
    name: str
    location: str | None = None
    floor: int
    min_pressure: float
    max_pressure: float


class SensorImportResponse(ApiModel):
    """
    Result of `POST /api/sensors/import`.

    With `dry_run` nothing is created: it is a preview of what would be
    created.
    """

    dry_run: bool
    site_id: UUID
    site_name: str
    created: int = Field(description="Sensors created: 0 in the preview.")
    sensors: list[SensorImportRow]
