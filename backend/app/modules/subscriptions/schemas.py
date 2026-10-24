# SCHEMAS — subscriptions
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de la suscripción (B14, issue #150).

    GET  /api/plans                      → list[PlanResponse]
    POST /api/me/organization/subscribe  → SubscriptionRequest → SubscriptionResponse

El NIF, el código postal y el IBAN no se validan en el schema sino en el
service, para responder con su código propio (`INVALID_TAX_ID`,
`INVALID_POSTAL_CODE`, `INVALID_IBAN`) en lugar del genérico
`VALIDATION_ERROR`, como el `INVALID_NAME` de la B1.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.shared.enums import BillingPeriod, OrganizationStatus, SubscriptionPlan
from app.shared.schemas import ApiModel, ApiRequest

# Topes del formulario: más que eso es un presupuesto a medida.
MAX_CONTRACT_SITES = 100
MAX_CONTRACT_SENSORS = 1000


class PlanResponse(ApiModel):
    """Un plan del catálogo. `None` en los límites es «sin límite»."""

    id: SubscriptionPlan
    name: str = Field(examples=["Profesional"])
    description: str
    monthly_price_eur: int = Field(
        description="Base del plan al mes en euros, IVA no incluido. Cada sensor se suma aparte."
    )
    sensor_price_eur: int = Field(description="Precio de cada sensor al mes, en euros.")
    yearly_months: int = Field(description="Meses que se pagan con el pago anual.")
    max_sites: int | None = Field(description="Edificios incluidos. `null`: sin límite.")
    max_sensors: int | None = Field(description="Sensores incluidos. `null`: sin límite.")
    features: list[str]


class SubscriptionRequest(ApiRequest):
    """
    Lo que contrata, datos fiscales y contacto del cliente que deja la prueba.

    No lleva el plan: sale de `sites` y `sensors`, y el precio también
    (ver `plans.py`). Los datos fiscales y la cuenta son obligatorios porque
    sin ellos no se puede facturar ni cobrar. El contacto es opcional: si no
    llega, se queda el que hay.
    """

    sites: int = Field(
        ge=1, le=MAX_CONTRACT_SITES,
        description="Edificios que contrata. No menos de los que ya tiene.",
        examples=[2],
    )
    sensors: int = Field(
        ge=1, le=MAX_CONTRACT_SENSORS,
        description=(
            "Sensores que contrata. Al menos uno por edificio y no menos de los "
            "que ya tiene."
        ),
        examples=[12],
    )
    billing_period: BillingPeriod = Field(
        description="`MONTHLY` (cada mes) o `YEARLY` (diez meses por adelantado)."
    )
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
        min_length=1, max_length=200, description="Dirección fiscal, sin el código postal.",
        examples=["Avinguda Diagonal 100"],
    )
    postal_code: str = Field(
        min_length=1, max_length=10, description="Código postal: cinco cifras.",
        examples=["08019"],
    )
    city: str = Field(
        min_length=1, max_length=120, description="Ciudad y provincia.",
        examples=["Barcelona"],
    )
    billing_email: EmailStr = Field(description="Email al que se envían las facturas.")
    contact_email: EmailStr | None = Field(default=None)
    phone: str | None = Field(default=None, max_length=30, examples=["+34 600 000 000"])
    iban: str = Field(
        min_length=1,
        max_length=42,
        description=(
            "Cuenta para domiciliar. Se comprueba y **solo se guarda "
            "enmascarada**: la API nunca la devuelve ni la almacena entera."
        ),
        examples=["ES91 2100 0418 4502 0005 1332"],
    )
    accept_terms: bool = Field(
        description="Tiene que ser `true`: acepta las condiciones de contratación."
    )
    accept_sepa: bool = Field(
        description="Tiene que ser `true`: autoriza la domiciliación SEPA del IBAN."
    )


class SubscriptionResponse(ApiModel):
    """La organización ya como cliente, con lo que se ha guardado."""

    organization_id: UUID
    organization_name: str
    status: OrganizationStatus
    plan: SubscriptionPlan
    plan_name: str = Field(examples=["Profesional"])
    billing_period: BillingPeriod
    contracted_sites: int = Field(examples=[2])
    contracted_sensors: int = Field(examples=[12])
    monthly_price_eur: int = Field(
        description="Precio al mes: base del plan más cada sensor, IVA no incluido.",
        examples=[199],
    )
    billed_price_eur: int = Field(
        description="Lo que se cobra cada vez: el mes, o diez meses si es anual.",
        examples=[199],
    )
    subscribed_at: datetime = Field(description="Momento de la suscripción, en UTC.")
    legal_name: str
    tax_id: str
    billing_address: str
    postal_code: str
    city: str
    billing_email: str
    contact_email: str | None = None
    phone: str | None = None
    iban_masked: str = Field(examples=["ES** **** **** **** **** 1332"])
    sepa_accepted_at: datetime = Field(
        description="Cuándo autorizó la domiciliación, en UTC."
    )
