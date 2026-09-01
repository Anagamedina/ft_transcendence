# SERVICE — alerts
# Reglas de negocio y orquestación. No hablar HTTP aquí.
# AlertService: reglas, acknowledge, resolve (transacciones).
"""
Lógica de alertas.

Las alertas las genera el backend, nunca el cliente: el documento es
explícito en que el simulador solo mide y que la detección de anomalías es
lógica de negocio (apartado 1.3). Por eso aquí no hay un `create`
público — la creación ocurre como efecto de registrar una lectura, desde
`ReadingService`.

Las tres reglas del MVP (apartado 1.2):

    presión < min_pressure del sensor   → LOW_PRESSURE
    presión > max_pressure del sensor   → HIGH_PRESSURE
    last_seen_at demasiado antiguo      → SENSOR_OFFLINE

Las dos primeras se evalúan al recibir una lectura. La tercera no: se
dispara por **ausencia** de datos, así que necesita algo que la compruebe
periódicamente. Es una diferencia importante de diseño y se resuelve en la
issue #28.

Implementación: issue #28.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotImplementedYetError
from app.modules.alerts.schemas import AlertResponse
from app.shared.dependencies import DbSession
from app.shared.schemas import Page


class AlertService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, offset: int, limit: int) -> Page[AlertResponse]:
        """Alertas visibles para el usuario, paginadas. Issue #28."""
        raise NotImplementedYetError("#28")

    def acknowledge(self, alert_id: UUID) -> AlertResponse:
        """
        Marca la alerta como reconocida: alguien la ha visto.

        Debe ser idempotente. Si dos operadores pulsan a la vez, la
        segunda llamada no debería fallar ni pisar la marca de tiempo de
        la primera; interesa saber cuándo se reconoció por primera vez.
        """
        raise NotImplementedYetError("#28")

    def resolve(self, alert_id: UUID) -> AlertResponse:
        """
        Cierra la alerta.

        Resolver una alerta ya resuelta es un `ConflictError`, no un
        éxito silencioso: cambiaría `resolved_at` y se perdería cuándo se
        atendió realmente.
        """
        raise NotImplementedYetError("#28")


def get_alert_service(db: DbSession) -> AlertService:
    """Proveedor del service para `Depends`."""
    return AlertService(db)
