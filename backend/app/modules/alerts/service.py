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

Las dos primeras se evalúan al recibir una lectura (`alerts/rules.py`). La
tercera no: se dispara por **ausencia** de datos, así que la comprueba
cada minuto una tarea de fondo (`alerts/offline.py`, arrancada desde
`main.py`).

Implementación: issue #28 (PRs #78, #98 y #118).
"""

from __future__ import annotations

from datetime import datetime, timezone

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.database import transaction
from app.core.exceptions import ConflictError, DomainValidationError, NotFoundError
from app.modules.alerts.repository import AlertRepository
from app.modules.alerts.schemas import AlertResponse, AlertState
from app.shared.dependencies import DbSession, _as_utc
from app.shared.schemas import Page


class AlertService:
    def __init__(self, db: Session, alerts: AlertRepository | None = None) -> None:
        self.db = db
        self.alerts = alerts or AlertRepository(db)

    def list(
        self,
        organization_id: UUID | None,
        offset: int,
        limit: int,
        status: str | None = None,
        sensor_id: UUID | None = None,
        q: str | None = None,
        organization_filter: UUID | None = None,
        site_id: UUID | None = None,
        severity: str | None = None,
        state: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
    ) -> Page[AlertResponse]:
        """
        Alertas de la organización, paginadas.

        `status` conserva el ciclo de vida guardado; `state` distingue las
        activas sin reconocer de las reconocidas. Gravedad y fechas se
        combinan con los filtros comunes antes de contar y paginar.

        `organization_id` sale siempre de `get_org_scope`: sin él,
        cualquiera vería las alertas de otro cliente. `None` significa
        «todas las organizaciones», y solo se da para un admin (issue #27).

        `q` busca en el mensaje y el nombre del sensor; `organization_filter`
        y `site_id` son los filtros comunes de la B0.
        """
        created_from = _as_utc(created_from) if created_from is not None else None
        created_to = _as_utc(created_to) if created_to is not None else None
        if created_from is not None and created_to is not None and created_from >= created_to:
            raise DomainValidationError(
                "`created_from` tiene que ser anterior a `created_to`.",
                code="INVALID_DATE_RANGE",
                details={"field": "created_from", "message": "Debe ser anterior a `created_to`."},
            )
        filas, total = self.alerts.list_by_organization(
            organization_id=organization_id,
            status=status,
            sensor_id=sensor_id,
            offset=offset,
            limit=limit,
            q=q,
            organization_filter=organization_filter,
            site_id=site_id,
            severity=severity,
            state=state,
            created_from=created_from,
            created_to=created_to,
        )
        return Page[AlertResponse](
            items=[self._to_response(f) for f in filas],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    def acknowledge(
        self, alert_id: UUID, organization_id: UUID | None, actor_id: UUID,
    ) -> AlertResponse:
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
        with transaction(self.db):
            alerta = self._propia_o_404(alert_id, organization_id)
            self.alerts.acknowledge(alerta.id, datetime.now(timezone.utc), actor_id)

        return self._to_response(alerta)

    def resolve(
        self, alert_id: UUID, organization_id: UUID | None, actor_id: UUID,
    ) -> AlertResponse:
        """
        Cierra la alerta.

        Resolver una ya resuelta es un `ConflictError`, no un éxito
        silencioso: volvería a escribir `resolved_at` y se perdería cuándo
        se atendió de verdad. Y esa fecha es el dato con el que luego se
        mide cuánto se tarda en responder.

        La comprobación se hace con la fila bloqueada para conservar la
        primera resolución incluso con dos peticiones simultáneas.
        """
        with transaction(self.db):
            alerta = self._propia_o_404(alert_id, organization_id)
            if alerta.status == "RESOLVED":
                raise ConflictError(
                    "Esa alerta ya estaba resuelta.",
                    code="ALERT_ALREADY_RESOLVED",
                )
            self.alerts.resolve(alerta.id, datetime.now(timezone.utc), actor_id)

        return self._to_response(alerta)

    def _propia_o_404(self, alert_id: UUID, organization_id: UUID | None):
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
        alerta = self.alerts.get_by_id(alert_id, organization_id, for_update=True)
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

        Los campos de lectura (B0) suben por `alerta → sensor → site →
        organization`. En los listados el repository ya los trae en bloque
        (`selectinload`), así que aquí no se hace una consulta por alerta.
        `state` se calcula con `AlertState.derive`.
        """
        sensor = alerta.sensor
        site = sensor.site
        return AlertResponse(
            id=alerta.id,
            sensor_id=alerta.sensor_id,
            sensor_name=sensor.name,
            site_id=site.id,
            site_name=site.name,
            organization_id=site.organization_id,
            organization_name=site.organization.name,
            floor=sensor.floor,
            type=alerta.alert_type,
            severity=alerta.severity,
            message=alerta.message,
            threshold=_limite(alerta.alert_type, sensor),
            status=alerta.status,
            state=AlertState.derive(alerta.status, alerta.acknowledged_at),
            created_at=_as_utc(alerta.created_at),
            acknowledged_at=_as_utc(alerta.acknowledged_at) if alerta.acknowledged_at else None,
            resolved_at=_as_utc(alerta.resolved_at) if alerta.resolved_at else None,
            acknowledged_by_name=(
                alerta.acknowledged_by_user.name if alerta.acknowledged_by_user else None
            ),
            resolved_by_name=(
                alerta.resolved_by_user.name if alerta.resolved_by_user else None
            ),
            resolution_minutes=(
                (_as_utc(alerta.resolved_at) - _as_utc(alerta.created_at)).total_seconds() / 60
                if alerta.status == "RESOLVED" and alerta.resolved_at is not None else None
            ),
        )


def _limite(alert_type: str, sensor) -> float | None:
    """El umbral que corresponde a la alerta (para pintar «1,1 bar · mín. 1,5»)."""
    valor = {
        "LOW_PRESSURE": sensor.low_threshold,
        "HIGH_PRESSURE": sensor.high_threshold,
    }.get(alert_type)
    return float(valor) if valor is not None else None


def get_alert_service(db: DbSession) -> AlertService:
    """Proveedor del service para `Depends`."""
    return AlertService(db)
