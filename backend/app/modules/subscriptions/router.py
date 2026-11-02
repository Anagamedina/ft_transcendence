# ROUTER — subscriptions
# Thin HTTP layer: validates schemas → calls the service → answers.
"""
"Hazte cliente" (become a client, B14, issue #150).

    GET  /api/plans                      → catalog, no session
    POST /api/me/organization/subscribe  → the client on trial subscribes to a plan

No `prefix`, like `users`: the two routes hang from different trees, and
the second goes under `/me` because it acts on the session organization,
not on one chosen by id.

`/plans` needs no session: they are public prices, the same the home page
can show.
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
    summary="Available plans",
    description=(
        "Fixed catalog of plans with price and limits. No session needed."
    ),
)
def list_plans(service: SubscriptionSvc) -> list[PlanResponse]:
    return service.list_plans()


@router.post(
    "/me/organization/subscribe",
    response_model=SubscriptionResponse,
    summary="Subscribe to a plan",
    description=(
        "The client on trial becomes a client (`TRIAL` → `ACTIVE`) with the "
        "buildings and sensors it contracts and its tax data. The API "
        "computes the plan and the price: plan base plus each sensor. It "
        "also works with an expired trial.\n\n"
        "The IBAN is mandatory (payment is by SEPA direct debit), must be "
        "Spanish (`ES` + 22 digits) and is stored masked only."
    ),
    responses={
        **error_response(status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."),
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "The session is not a client one (`FORBIDDEN`).",
        ),
        **error_response(
            status.HTTP_409_CONFLICT,
            "The organization is not on trial (`ORGANIZATION_NOT_IN_TRIAL`) or "
            "it contracts fewer buildings or sensors than it already has "
            "(`CONTRACT_BELOW_CURRENT`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Fewer sensors than buildings (`SENSORS_BELOW_SITES`), conditions "
            "not accepted (`TERMS_NOT_ACCEPTED`), direct debit not authorized "
            "(`SEPA_NOT_ACCEPTED`), malformed tax id (`INVALID_TAX_ID`), wrong "
            "postal code (`INVALID_POSTAL_CODE`), phone that is not Spanish "
            "(`INVALID_PHONE`) or wrong IBAN "
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
