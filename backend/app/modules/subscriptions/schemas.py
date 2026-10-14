# SCHEMAS — subscriptions
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de la suscripción (B14, issue #150).

    GET  /api/plans                      → list[PlanResponse]
    POST /api/me/organization/subscribe  → SubscriptionRequest → SubscriptionResponse

El NIF y el IBAN no se validan en el schema sino en el service, para
responder con su código propio (`INVALID_TAX_ID`, `INVALID_IBAN`) en lugar
del genérico `VALIDATION_ERROR`, como el `INVALID_NAME` de la B1.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.shared.enums import OrganizationStatus, SubscriptionPlan
from app.shared.schemas import ApiModel, ApiRequest


class PlanResponse(ApiModel):
    """Un plan del catálogo. `None` en los límites es «sin límite»."""

    id: SubscriptionPlan
    name: str = Field(examples=["Profesional"])
    description: str
    monthly_price_eur: int = Field(description="Precio al mes en euros, IVA no incluido.")
    max_sites: int | None = Field(description="Edificios incluidos. `null`: sin límite.")
    max_sensors: int | None = Field(description="Sensores incluidos. `null`: sin límite.")
    features: list[str]


class SubscriptionRequest(ApiRequest):
    """
    Plan, datos fiscales y contacto del cliente que deja la prueba.

    Los datos fiscales son obligatorios porque sin ellos no se puede
    facturar. El contacto es opcional: si no llega, se queda el que hay.
    """

    plan: SubscriptionPlan
    legal_name: str = Field(
        min_length=1, max_length=200, description="Razón social.",
        examples=["Hoteles Diagonal S.L."],
    )
    tax_id: str = Field(
        min_length=1, max_length=30,
        description="NIF, NIE o CIF. Se guarda en mayúsculas y sin espacios ni guiones.",
        examples=["B12345678"],
    )
    billing_address: str = Field(
        min_length=1, max_length=200, description="Dirección fiscal.",
        examples=["Avinguda Diagonal 100, 08019"],
    )
    city: str | None = Field(default=None, max_length=120, examples=["Barcelona"])
    billing_email: EmailStr = Field(description="Email al que se envían las facturas.")
    contact_email: EmailStr | None = Field(default=None)
    phone: str | None = Field(default=None, max_length=30, examples=["+34 600 000 000"])
    iban: str | None = Field(
        default=None,
        max_length=42,
        description=(
            "Cuenta para domiciliar, opcional. Se comprueba y **solo se guarda "
            "enmascarada**: la API nunca la devuelve ni la almacena entera."
        ),
        examples=["ES91 2100 0418 4502 0005 1332"],
    )
    accept_terms: bool = Field(
        description="Tiene que ser `true`: acepta las condiciones de contratación."
    )


class SubscriptionResponse(ApiModel):
    """La organización ya como cliente, con lo que se ha guardado."""

    organization_id: UUID
    organization_name: str
    status: OrganizationStatus
    plan: SubscriptionPlan
    plan_name: str = Field(examples=["Profesional"])
    subscribed_at: datetime = Field(description="Momento de la suscripción, en UTC.")
    legal_name: str
    tax_id: str
    billing_address: str
    city: str | None = None
    billing_email: str
    contact_email: str | None = None
    phone: str | None = None
    iban_masked: str | None = Field(
        default=None, examples=["ES** **** **** **** **** 1332"]
    )
