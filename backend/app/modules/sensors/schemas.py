# SCHEMAS — sensors
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de sensores (issue #23).

Campos según el modelo de dominio del documento de arquitectura
(apartado 5):

    sensors: id, site_id, name, location, sensor_type,
             min_pressure, max_pressure, status, last_seen_at, created_at

Dos cosas que conviene entender de este módulo:

**Los umbrales viven en el sensor, no en la regla de alerta.** Cada sensor
tiene su `min_pressure` y `max_pressure` porque la presión normal de un
depósito no es la de una planta 12. La issue #28 comparará cada lectura
con los umbrales de *su* sensor para decidir si hay LOW_PRESSURE o
HIGH_PRESSURE.

**`last_seen_at` es la base de la tercera alerta.** SENSOR_OFFLINE no se
detecta por lo que llega, sino por lo que deja de llegar: si
`last_seen_at` se aleja demasiado del momento actual, el sensor está
mudo. Por eso el campo está en el sensor y no en las lecturas.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator, model_validator

# SensorType y SensorStatus viven en shared/enums.py (B0); se reexportan
# desde aquí porque el resto del código ya los importa de este módulo.
from app.shared.enums import SensorStatus, SensorType
from app.shared.schemas import ApiModel, ApiRequest

# Límite físico del rango de medida que aceptamos para un sensor de
# presión de instalación interna, en bar. La presión de servicio real de
# un edificio ronda 1–6 bar; el margen hasta 25 cubre picos y golpe de
# ariete sin dar por buena una lectura absurda como 900.
#
# La tabla `sensors` aplica este mismo rango a los umbrales con el CHECK
# `ck_sensors_threshold_range` (issue #97): si se cambia aquí, hay que
# cambiarlo también allí con una migración.
PRESSURE_MIN_BAR = 0.0
PRESSURE_MAX_BAR = 25.0


class SensorBase(ApiRequest):
    name: str = Field(
        min_length=1,
        max_length=120,
        description="Nombre del sensor.",
        examples=["Sensor cocina"],
    )
    location: str | None = Field(
        default=None,
        max_length=120,
        description="Zona del edificio donde está instalado.",
        examples=["Planta 1 - Cocina"],
    )
    sensor_type: SensorType = Field(
        default=SensorType.PRESSURE,
        description="Magnitud medida.",
    )
    min_pressure: float = Field(
        ge=PRESSURE_MIN_BAR,
        le=PRESSURE_MAX_BAR,
        description="Umbral inferior en bar. Por debajo se genera LOW_PRESSURE.",
        examples=[1.5],
    )
    max_pressure: float = Field(
        ge=PRESSURE_MIN_BAR,
        le=PRESSURE_MAX_BAR,
        description="Umbral superior en bar. Por encima se genera HIGH_PRESSURE.",
        examples=[6.0],
    )

    @field_validator("name")
    @classmethod
    def _nombre_no_vacio(cls, valor: str) -> str:
        """
        `min_length=1` no recorta: `"   "` lo pasaría. Se quitan los espacios
        de los extremos y, si no queda nada, se rechaza (#29).
        """
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío.")
        return valor

    @model_validator(mode="after")
    def _check_threshold_order(self) -> "SensorBase":
        """
        Validación entre campos: el mínimo tiene que ser menor que el máximo.

        `Field(ge=..., le=...)` solo puede mirar un campo por separado, así
        que `min_pressure=8` con `max_pressure=2` pasaría esa capa sin
        problema. Un `model_validator(mode="after")` se ejecuta cuando el
        objeto ya está construido y sí puede comparar los dos.

        Sin esto el sensor quedaría en un estado imposible: toda lectura
        sería a la vez demasiado baja y demasiado alta.
        """
        if self.min_pressure >= self.max_pressure:
            raise ValueError("min_pressure debe ser menor que max_pressure")
        return self


class SensorCreate(SensorBase):
    """
    Alta de sensor (`POST /api/sensors`, issue #29).

    `site_id` sí se envía aquí, a diferencia de `organization_id` en sites:
    el admin elige en qué edificio instala el sensor. Solo un admin puede
    dar de alta sensores, y un admin ve todas las organizaciones (#27), así
    que el service solo comprueba que el site exista (404 si no).
    """

    site_id: UUID = Field(description="Site donde se instala el sensor.")
    external_id: str = Field(
        min_length=1,
        max_length=100,
        description=(
            "Etiqueta del aparato físico o del fabricante, distinta del id "
            "interno. Única dentro de su site: repetirla da 409."
        ),
        examples=["SENS-001"],
    )
    unit: str = Field(
        default="bar",
        min_length=1,
        max_length=20,
        description="Unidad de medida. Si no se envía, `bar`.",
        examples=["bar"],
    )


class SensorUpdate(ApiRequest):
    """
    Modificación parcial (`PATCH /api/sensors/{id}`, issue #29).

    No incluye `status` ni `last_seen_at`: los mantiene el backend a
    partir de las lecturas recibidas. Si el cliente pudiera escribirlos,
    podría marcar como ONLINE un sensor que lleva días mudo.
    """

    name: str | None = Field(default=None, min_length=1, max_length=120)
    location: str | None = Field(default=None, max_length=120)
    min_pressure: float | None = Field(
        default=None, ge=PRESSURE_MIN_BAR, le=PRESSURE_MAX_BAR
    )
    max_pressure: float | None = Field(
        default=None, ge=PRESSURE_MIN_BAR, le=PRESSURE_MAX_BAR
    )

    @field_validator("name")
    @classmethod
    def _nombre_no_vacio(cls, valor: str | None) -> str | None:
        """Igual que en el alta. `None` lo trata el service (no se puede borrar)."""
        if valor is None:
            return None
        valor = valor.strip()
        if not valor:
            raise ValueError("El nombre no puede estar vacío.")
        return valor

    @model_validator(mode="after")
    def _check_threshold_order(self) -> "SensorUpdate":
        """
        Aquí solo se puede comparar si llegan los dos umbrales a la vez.

        Si el PATCH trae únicamente `max_pressure`, hay que contrastarlo
        con el `min_pressure` que ya está guardado, y eso requiere leer el
        sensor: es una comprobación de negocio y la hace el service, no el
        schema.
        """
        if self.min_pressure is not None and self.max_pressure is not None:
            if self.min_pressure >= self.max_pressure:
                raise ValueError("min_pressure debe ser menor que max_pressure")
        return self


class SensorResponse(ApiModel):
    id: UUID
    site_id: UUID
    # Campos de lectura (B0): para que las listas pinten el edificio y el
    # cliente sin pedirlos aparte.
    site_name: str = Field(description="Nombre del edificio.")
    organization_id: UUID = Field(description="Organización del edificio.")
    organization_name: str = Field(description="Nombre de la organización.")
    floor: int = Field(
        description="Planta donde está el sensor. 0 es la baja; negativo, sótano."
    )
    external_id: str = Field(
        description="Etiqueta del aparato físico (`SENS-001`), única en su site."
    )
    name: str
    location: str | None = None
    sensor_type: SensorType
    unit: str = Field(description="Unidad de las lecturas y de los umbrales.")
    min_pressure: float = Field(description="Umbral inferior en bar.")
    max_pressure: float = Field(description="Umbral superior en bar.")
    status: SensorStatus = Field(description="Estado operativo calculado.")
    last_seen_at: datetime | None = Field(
        default=None,
        description=(
            "Última vez que se recibió una lectura de este sensor, en UTC. "
            "Nulo si nunca ha enviado ninguna."
        ),
    )
    created_at: datetime
