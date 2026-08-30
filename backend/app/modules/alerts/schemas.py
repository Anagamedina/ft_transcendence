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
DECISIÓN ABIERTA — cómo se representa "acknowledge"
--------------------------------------------------------------------
El apartado 9.1 define dos endpoints distintos:

    PATCH /api/alerts/{id}/acknowledge
    PATCH /api/alerts/{id}/resolve

pero `status` solo admite ACTIVE y RESOLVED. Faltaría poder distinguir
"alguien la ha visto y está en ello" de "sigue sin atender". Dos salidas:

  a) Añadir un tercer estado ACKNOWLEDGED al enum.
  b) Mantener los dos estados y añadir una columna `acknowledged_at`.

Se propone (b), y es lo que refleja este contrato. Motivo: reconocer y
resolver son hechos independientes, no fases de una misma escala. Con un
enum de tres valores se pierde la información de quién reconoció una
alerta en cuanto alguien la resuelve, y no se puede resolver una alerta
que nadie llegó a reconocer sin inventar transiciones.

Requiere columna nueva, así que **hay que confirmarlo con Daruny antes de
la migración de Alembic** (issues #12, #13 y #18).
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import Field

from app.shared.schemas import ApiModel


class AlertType(str, Enum):
    """Regla que disparó la alerta. Los tres casos del apartado 1.2."""

    LOW_PRESSURE = "LOW_PRESSURE"
    HIGH_PRESSURE = "HIGH_PRESSURE"
    SENSOR_OFFLINE = "SENSOR_OFFLINE"


class AlertSeverity(str, Enum):
    """
    Gravedad.

    Es distinta del tipo: una presión baja puede ser WARNING si roza el
    umbral y CRITICAL si se desploma. Qué combinación corresponde a cada
    caso lo decide la issue #28.
    """

    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    """Ciclo de vida. Valores tal y como los fija el documento."""

    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"


class AlertResponse(ApiModel):
    id: UUID
    sensor_id: UUID = Field(description="Sensor que originó la alerta.")
    type: AlertType
    severity: AlertSeverity
    message: str = Field(
        description="Descripción legible del problema.",
        examples=["Presión por debajo del umbral: 0.8 bar (mínimo 1.5)"],
    )
    status: AlertStatus
    created_at: datetime = Field(description="Cuándo se generó, en UTC.")
    acknowledged_at: datetime | None = Field(
        default=None,
        description=(
            "Cuándo se reconoció la alerta, en UTC. Nulo si nadie la ha "
            "reconocido todavía. Campo pendiente de confirmar con Daruny "
            "(ver nota del módulo)."
        ),
    )
    resolved_at: datetime | None = Field(
        default=None,
        description="Cuándo se resolvió, en UTC. Nulo mientras siga activa.",
    )
