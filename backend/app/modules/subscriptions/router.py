# ROUTER — subscriptions
# Capa HTTP fina: valida schemas → llama service → responde.
"""
«Hazte cliente» (B14, issue #150).

    GET  /api/plans                      → catálogo, sin sesión
    POST /api/me/organization/subscribe  → el cliente en prueba contrata un plan

Sin `prefix`, como `users`: las dos rutas cuelgan de árboles distintos, y
la segunda va bajo `/me` porque actúa sobre la organización de la sesión,
no sobre una que se elige por id.

`/plans` no pide sesión: son precios públicos, los mismos que puede
enseñar la portada.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.modules.subscriptions.schemas import (
    PlanResponse,
    SubscriptionRequest,
    SubscriptionResponse,
)
from app.modules.subscriptions.service import (
    SubscriptionService,
    get_subscription_service,
)
from app.modules.users.model import User
from app.shared.dependencies import require_role
from app.shared.schemas import error_response

router = APIRouter(tags=["Subscriptions"])

SubscriptionSvc = Annotated[SubscriptionService, Depends(get_subscription_service)]


@router.get(
    "/plans",
    response_model=list[PlanResponse],
    summary="Planes disponibles",
    description=(
        "Catálogo fijo de planes con precio y límites. No necesita sesión."
    ),
)
def list_plans(service: SubscriptionSvc) -> list[PlanResponse]:
    return service.list_plans()


@router.post(
    "/me/organization/subscribe",
    response_model=SubscriptionResponse,
    summary="Contratar un plan",
    description=(
        "El cliente en prueba pasa a cliente (`TRIAL` → `ACTIVE`) con los "
        "edificios y sensores que contrata y sus datos fiscales. El plan y el "
        "precio los calcula la API: base del plan más cada sensor. Vale "
        "también con la prueba caducada.\n\n"
        "El IBAN es obligatorio (se paga por domiciliación SEPA) y solo se "
        "guarda enmascarado."
    ),
    responses={
        **error_response(status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."),
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "La sesión no es de un cliente (`FORBIDDEN`).",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "La organización no está en prueba (`ORGANIZATION_NOT_IN_TRIAL`) o "
            "contrata menos edificios o sensores de los que ya tiene "
            "(`CONTRACT_BELOW_CURRENT`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Menos sensores que edificios (`SENSORS_BELOW_SITES`), "
            "condiciones sin aceptar (`TERMS_NOT_ACCEPTED`), domiciliación sin "
            "autorizar (`SEPA_NOT_ACCEPTED`), NIF mal escrito (`INVALID_TAX_ID`), "
            "código postal incorrecto (`INVALID_POSTAL_CODE`), teléfono que no es "
            "español (`INVALID_PHONE`) o IBAN incorrecto "
            "(`INVALID_IBAN`).",
        ),
    },
)
def subscribe(
    payload: SubscriptionRequest,
    service: SubscriptionSvc,
    user: Annotated[User, Depends(require_role("client"))],
) -> SubscriptionResponse:
    return service.subscribe(user, payload)
