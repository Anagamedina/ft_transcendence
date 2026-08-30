# SCHEMAS — readings
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de lecturas (issue #23).

Es el contrato más importante del proyecto: `POST /api/readings` es el
primer eslabón del flujo vertical que el documento marca como primera
funcionalidad obligatoria (apartado 8.5).

    Simulator → POST /api/readings → FastAPI → Service → Repository → PostgreSQL

--------------------------------------------------------------------
LOS DOS TIEMPOS DE UNA LECTURA
--------------------------------------------------------------------
El apartado 5 del documento declara la columna como `created_at`, pero la
regla 5.1 pide «Índice en readings (sensor_id, measured_at)». No es una
errata: son dos momentos distintos y el contrato necesita los dos.

    measured_at → cuándo el sensor tomó la medida.  Lo pone quien mide.
    created_at  → cuándo el backend la registró.    Lo pone el servidor.

Con el simulador dentro de la misma red de Docker los dos valores se
diferencian en milisegundos, y por eso es fácil creer que sobra uno. Con
sensores reales no: una pasarela sin cobertura puede acumular lecturas y
enviarlas media hora después. Si solo se guarda el instante de inserción,
la gráfica del histórico dibuja esas lecturas apiladas en el momento en
que llegaron, no cuando ocurrieron, y el pico de presión aparece a la
hora equivocada.

`measured_at` es **opcional en la entrada**: si el emisor no lo manda, el
servidor usa el momento de recepción. Así el simulador puede empezar sin
él y añadirlo después sin romper nada.

El índice `(sensor_id, measured_at)` de la regla 5.1 es exactamente lo que
necesita la consulta del histórico —filtrar por sensor y ordenar por
fecha, esas dos columnas y en ese orden—, lo que confirma que la ordenación
del histórico va por `measured_at`, no por `created_at`.

Pendiente: que Daruny incluya ambas columnas en el modelo `Reading`
(issue #13) antes de la primera migración de Alembic.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.modules.sensors.schemas import PRESSURE_MAX_BAR, PRESSURE_MIN_BAR
from app.shared.schemas import ApiModel, ApiRequest


class ReadingCreate(ApiRequest):
    """
    Lectura entrante. Es lo que envía el simulador (issue #16, Daruny).

    El rango de `pressure` se comparte con `sensors` importando las
    constantes en vez de repetir los números: si mañana se decide que el
    máximo es 16 bar, se cambia en un sitio y no quedan dos validaciones
    discrepando entre el sensor y sus lecturas.

    Ojo con la diferencia entre este rango y los umbrales del sensor:

    - Fuera de 0–25 bar  → la lectura es **inválida**, se rechaza con 422.
      Ningún sensor de instalación interna mide eso; es un fallo de envío.
    - Fuera de min/max del sensor → la lectura es **válida y se guarda**,
      y además genera una alerta (issue #28).

    Confundirlos haría que las lecturas anómalas —justo las que interesan—
    se descarten en lugar de alertar.

    Como hereda de `ApiRequest`, un campo de más se rechaza. Si el
    simulador manda `sensorId` en vez de `sensor_id`, la respuesta es 422
    y no se guarda nada: es preferible a aceptarlo y perder el dato en
    silencio.
    """

    sensor_id: UUID = Field(
        description="Sensor que emite la lectura.",
        examples=["6f1c8a2e-6b3d-4f9a-9c21-0b7e5d3a9d4b"],
    )
    pressure: float = Field(
        ge=PRESSURE_MIN_BAR,
        le=PRESSURE_MAX_BAR,
        description=(
            f"Presión medida en bar. Rango aceptado: "
            f"{PRESSURE_MIN_BAR}–{PRESSURE_MAX_BAR}. Fuera de rango es un "
            f"error de envío (422), no una anomalía."
        ),
        examples=[3.42],
    )
    measured_at: datetime | None = Field(
        default=None,
        description=(
            "Cuándo tomó la medida el sensor, en ISO-8601 UTC terminado en "
            "`Z`. **Opcional**: si no se envía, el servidor usa el momento "
            "de recepción."
        ),
        examples=["2026-08-21T09:15:00Z"],
    )


class ReadingResponse(ApiModel):
    """
    Lectura tal y como se devuelve, en `POST /api/readings` (issue #24) y
    en `GET /api/sensors/{id}/readings` (issue #25).

    En el diagrama de arquitectura este schema aparece como
    `ReadingPublic`. Aquí se llama `ReadingResponse` para que todos los
    módulos usen el mismo sufijo (`UserResponse`, `SensorResponse`,
    `ErrorResponse`). Solo cambia el nombre del schema en OpenAPI; los
    campos del JSON son idénticos.
    """

    id: UUID = Field(description="Identificador de la lectura. Lo genera la base.")
    sensor_id: UUID
    pressure: float = Field(description="Presión medida en bar.")
    measured_at: datetime = Field(
        description=(
            "Cuándo se tomó la medida, en UTC. Siempre presente en la "
            "respuesta: si no se envió, es igual a `created_at`."
        )
    )
    created_at: datetime = Field(
        description="Cuándo se registró en el backend, en UTC."
    )
