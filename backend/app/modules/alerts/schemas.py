# SCHEMAS — alerts
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de alertas (issue #23).

Campos según el modelo de dominio del documento (apartado 5):

    alerts: id, sensor_id, type, severity, message, status,
            created_at, resolved_at

    type     → LOW_PRESSURE | HIGH_PRESSURE | SENSOR_OFFLINE
    status   → ACTIVE | RESOLVED
    severity → WARNING | CRITICAL

Las alertas las **crea el backend**, nunca el cliente: el documento es
explícito en que el simulador solo genera mediciones y que la detección
de anomalías es lógica de negocio (apartado 1.3). Por eso no existe un
`AlertCreate` en este contrato — no hay `POST /api/alerts`. Solo se
listan y se cambia su estado.

--------------------------------------------------------------------
"Acknowledge": estado guardado frente a estado calculado
--------------------------------------------------------------------
El apartado 9.1 define dos endpoints distintos:

    PATCH /api/alerts/{id}/acknowledge
    PATCH /api/alerts/{id}/resolve

La tabla solo guarda `status` ACTIVE / RESOLVED, más `acknowledged_at`
(decidido con Daruny antes de la migración). Reconocer y resolver son
hechos independientes, no fases de una misma escala: con un enum de tres
valores en la tabla se perdería cuándo se reconoció una alerta en cuanto
alguien la resuelve.

Las pantallas sí quieren un único estado de tres valores. Por eso la
respuesta trae `state` (`AlertState`, B0), calculado a partir de los dos
campos guardados. Ver `shared/enums.py`.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

# Los enums viven en shared/enums.py (B0); se reexportan desde aquí
# porque reglas, service y tests ya los importan de este módulo.
from app.shared.enums import AlertSeverity, AlertState, AlertStatus, AlertType
from app.shared.schemas import ApiModel


class AlertResponse(ApiModel):
    id: UUID
    sensor_id: UUID = Field(description="Sensor que originó la alerta.")
    # Campos de lectura (B0): para pintar «Hotel Sol · Planta 2 · Sensor
    # bombas» sin pedir el sensor, el site y la organización por separado.
    sensor_name: str = Field(description="Nombre del sensor.")
    site_id: UUID = Field(description="Edificio del sensor.")
    site_name: str = Field(description="Nombre del edificio.")
    organization_id: UUID = Field(description="Organización del edificio.")
    organization_name: str = Field(description="Nombre de la organización.")
    floor: int = Field(
        description="Planta del sensor. 0 es la baja; negativo, sótano."
    )
    type: AlertType
    severity: AlertSeverity
    message: str = Field(
        description="Descripción legible del problema.",
        examples=["Presión por debajo del umbral: 0.8 bar (mínimo 1.5)"],
    )
    status: AlertStatus = Field(
        description="Estado guardado: ACTIVE o RESOLVED. Ver también `state`."
    )
    state: AlertState = Field(
        description=(
            "Estado para las pantallas, calculado: RESOLVED si está "
            "resuelta, ACKNOWLEDGED si sigue activa pero alguien la ha "
            "reconocido, ACTIVE si nadie la ha reconocido."
        )
    )
    created_at: datetime = Field(description="Cuándo se generó, en UTC.")
    acknowledged_at: datetime | None = Field(
        default=None,
        description=(
            "Cuándo se reconoció la alerta, en UTC. Nulo si nadie la ha "
            "reconocido todavía."
        ),
    )
    resolved_at: datetime | None = Field(
        default=None,
        description="Cuándo se resolvió, en UTC. Nulo mientras siga activa.",
    )
