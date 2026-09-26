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

from datetime import datetime, timezone

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import transaction
from app.core.exceptions import ConflictError, NotFoundError, NotImplementedYetError
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.schemas import AlertResponse
from app.shared.dependencies import DbSession
from app.shared.schemas import Page


class AlertService:
    def __init__(self, db: Session, alerts: AlertRepository | None = None) -> None:
        self.db = db
        self.alerts = alerts or AlertRepository(db)

    def list(
        self,
        organization_id: UUID,
        offset: int,
        limit: int,
        status: str | None = None,
        sensor_id: UUID | None = None,
    ) -> Page[AlertResponse]:
        """
        Alertas de la organización, paginadas.

        Los dos filtros son los que pide el panel: `status` para ver solo
        las activas, que es la vista por defecto de quien atiende, y
        `sensor_id` para entrar desde el detalle de un sensor.

        `organization_id` sale de la sesión y no es opcional: sin él,
        cualquiera vería las alertas de otro cliente.
        """
        filas, total = self.alerts.list_by_organization(
            organization_id=organization_id,
            status=status,
            sensor_id=sensor_id,
            offset=offset,
            limit=limit,
        )
        return Page[AlertResponse](
            items=[self._to_response(f) for f in filas],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    def acknowledge(self, alert_id: UUID, organization_id: UUID) -> AlertResponse:
        """
        Marca la alerta como reconocida: alguien la ha visto.

        Es idempotente. Si dos operadores pulsan a la vez, la segunda
        llamada no falla ni pisa la marca de tiempo de la primera:
        interesa saber cuándo se reconoció por PRIMERA vez, no la última
        vez que alguien hizo clic. Esa garantía la da el repository, que
        solo escribe si el campo estaba vacío.

        Reconocer no es resolver: la alerta sigue activa, solo consta que
        alguien está al tanto.
        """
        alerta = self._propia_o_404(alert_id, organization_id)

        with transaction(self.db):
            self.alerts.acknowledge(alerta.id, datetime.now(timezone.utc))

        return self._to_response(alerta)

    def resolve(self, alert_id: UUID, organization_id: UUID) -> AlertResponse:
        """
        Cierra la alerta.

        Resolver una ya resuelta es un `ConflictError`, no un éxito
        silencioso: volvería a escribir `resolved_at` y se perdería cuándo
        se atendió de verdad. Y esa fecha es el dato con el que luego se
        mide cuánto se tarda en responder.

        Aquí no se puede delegar en el repository como en `acknowledge`:
        el suyo sobrescribe sin mirar, así que la comprobación va antes.
        """
        alerta = self._propia_o_404(alert_id, organization_id)

        if alerta.status == "RESOLVED":
            raise ConflictError(
                "Esa alerta ya estaba resuelta.",
                code="ALERT_ALREADY_RESOLVED",
            )

        with transaction(self.db):
            self.alerts.resolve(alerta.id, datetime.now(timezone.utc))

        return self._to_response(alerta)

    def _propia_o_404(self, alert_id: UUID, organization_id: UUID):
        """
        La alerta, solo si es de esa organización.

        Se comprueba aquí porque `acknowledge` y `resolve` del repository
        buscan por id a secas, sin filtrar. Sin este paso, cualquiera que
        acertara el id de una alerta ajena podría darla por vista o
        cerrarla.

        Una alerta de otra organización responde lo mismo que una que no
        existe: decir «existe pero no es tuya» ya confirma que ese
        identificador es real.
        """
        alerta = self.alerts.get_by_id(alert_id, organization_id)
        if alerta is None:
            raise NotFoundError(
                "La alerta indicada no existe.",
                code="ALERT_NOT_FOUND",
            )
        return alerta

    @staticmethod
    def _to_response(alerta) -> AlertResponse:
        """
        Convierte la fila al schema de salida.

        No sirve `model_validate` directo: el contrato llama `type` a lo
        que la tabla guarda como `alert_type`. Es el mismo desajuste de
        vocabulario que ya se traduce en readings, y se resuelve donde
        toca — en el service, que conoce los dos lados.
        """
        return AlertResponse(
            id=alerta.id,
            sensor_id=alerta.sensor_id,
            type=alerta.alert_type,
            severity=alerta.severity,
            message=alerta.message,
            status=alerta.status,
            created_at=alerta.created_at,
            acknowledged_at=alerta.acknowledged_at,
            resolved_at=alerta.resolved_at,
        )


def get_alert_service(db: DbSession) -> AlertService:
    """Proveedor del service para `Depends`."""
    return AlertService(db)
