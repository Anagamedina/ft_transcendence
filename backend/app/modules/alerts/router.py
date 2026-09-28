    # ROUTER — alerts
# Capa HTTP fina: valida schemas → llama service → responde.
# AlertService: reglas, acknowledge, resolve (transacciones).
"""
Endpoints de alertas (`/api/alerts/...`).

Registrado desde la issue #22, **sin rutas todavía**. Las del nivel
Básico son de la issue #28:

    GET   /api/alerts
    PATCH /api/alerts/{id}/acknowledge
    PATCH /api/alerts/{id}/resolve

Dos decisiones ya tomadas para cuando se implementen:

**PATCH y no POST.** Es lo que fija el apartado 9.1 del documento. (El
diagrama de arquitectura dibuja `POST .../resolve` y omite
`acknowledge`; manda el documento, que es el acuerdo del equipo.) PATCH
porque no se sustituye la alerta entera, solo una parte de su estado.

**Dos rutas y no un `PATCH /api/alerts/{id}` con un campo `status`.**
Reconocer y resolver no son dos formas de escribir lo mismo: son acciones
distintas, con efectos y permisos distintos, y separarlas permite
autorizarlas por separado.

No habrá `POST /api/alerts`: las alertas las crea el backend al procesar
lecturas, nunca el cliente (apartado 1.3).
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.modules.alerts.schemas import AlertResponse, AlertStatus
from app.modules.alerts.service import AlertService, get_alert_service
from app.shared.dependencies import CurrentUser, Pagination
from app.shared.schemas import Page, error_response

router = APIRouter(prefix="/alerts", tags=["Alerts"])

AlertSvc = Annotated[AlertService, Depends(get_alert_service)]

_NO_AUTORIZADO = error_response(
    status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."
)
_NO_ENCONTRADA = error_response(
    status.HTTP_404_NOT_FOUND,
    "La alerta no existe, o no es de tu organización (`ALERT_NOT_FOUND`).",
)


@router.get(
    "",
    response_model=Page[AlertResponse],
    summary="Listar alertas",
    description=(
        "Alertas de tu organización, paginadas.\n\n"
        "Los dos filtros son los que usa el panel: `status` para ver solo "
        "las activas, que es la vista por defecto de quien atiende, y "
        "`sensor_id` para entrar desde el detalle de un sensor."
    ),
    responses={**_NO_AUTORIZADO},
)
def list_alerts(
    service: AlertSvc,
    user: CurrentUser,
    pagination: Pagination,
    status_filtro: Annotated[
        AlertStatus | None,
        Query(alias="status", description="Deja solo las alertas en ese estado."),
    ] = None,
    sensor_id: Annotated[
        UUID | None,
        Query(description="Deja solo las alertas de ese sensor."),
    ] = None,
) -> Page[AlertResponse]:
    # La organización sale de la sesión, nunca de la query: si viniera de
    # fuera, cualquiera pediría las alertas de otro cliente.
    return service.list(
        organization_id=user.organization_id,
        offset=pagination.offset,
        limit=pagination.limit,
        status=status_filtro.value if status_filtro else None,
        sensor_id=sensor_id,
    )


@router.patch(
    "/{alert_id}/acknowledge",
    response_model=AlertResponse,
    summary="Marcar una alerta como vista",
    description=(
        "Deja constancia de que alguien está al tanto de la alerta.\n\n"
        "**No la cierra:** la alerta sigue activa. Y es idempotente — si "
        "dos operadores pulsan a la vez, la segunda llamada no falla ni "
        "pisa la hora de la primera, que es la que interesa conservar."
    ),
    responses={**_NO_AUTORIZADO, **_NO_ENCONTRADA},
)
def acknowledge_alert(
    alert_id: UUID, service: AlertSvc, user: CurrentUser
) -> AlertResponse:
    return service.acknowledge(alert_id, organization_id=user.organization_id)


@router.patch(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
    summary="Cerrar una alerta",
    description=(
        "Da la alerta por atendida.\n\n"
        "Resolver una ya resuelta responde **409**, no un éxito "
        "silencioso: volvería a escribir la fecha de cierre y se perdería "
        "cuándo se atendió de verdad."
    ),
    responses={
        **_NO_AUTORIZADO,
        **_NO_ENCONTRADA,
        **error_response(
            status.HTTP_409_CONFLICT,
            "La alerta ya estaba resuelta (`ALERT_ALREADY_RESOLVED`).",
        ),
    },
)
def resolve_alert(
    alert_id: UUID, service: AlertSvc, user: CurrentUser
) -> AlertResponse:
    return service.resolve(alert_id, organization_id=user.organization_id)
