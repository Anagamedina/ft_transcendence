# SCHEMAS — organizations
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de organizaciones (issue #23).

La organización es el cliente de AquaGuard: una comunidad, un municipio o
una empresa. Es además la **unidad de aislamiento** de todo el sistema.

    organization → sites → sensors → readings → alerts

Todo cuelga de ella, y esa cadena es lo que permite responder a la
pregunta "¿puede este usuario ver esta lectura?" subiendo por las
relaciones hasta la organización. El aislamiento lo aplica
`get_org_scope` (issue #27), y el contrato lo refleja exponiendo
`organization_id` en los recursos que dependen de ella.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.modules.sites.schemas import SiteCreate
from app.shared.enums import OrganizationStatus
from app.shared.schemas import ApiModel, ApiRequest

# Los nombres de organización se guardan con 120 caracteres como máximo
# (columna `name` y migración de la #120).
NAME_MAX = 120


class OrganizationContact(ApiRequest):
    """
    Datos de contacto y de facturación (B1, columnas de la D1).

    Todos opcionales: el admin da de alta un cliente con el nombre y va
    completando lo demás. Los emails se validan como email; el resto es
    texto libre con el mismo largo que su columna.
    """

    city: str | None = Field(default=None, max_length=120, examples=["Barcelona"])
    contact_email: EmailStr | None = Field(
        default=None, description="Email de contacto del cliente."
    )
    phone: str | None = Field(default=None, max_length=30, examples=["+34 600 000 000"])
    legal_name: str | None = Field(
        default=None, max_length=200, description="Razón social.",
        examples=["Hoteles Diagonal S.L."],
    )
    tax_id: str | None = Field(
        default=None, max_length=30, description="NIF o CIF.", examples=["B12345678"]
    )
    billing_email: EmailStr | None = Field(
        default=None, description="Email al que se envían las facturas."
    )


class OrganizationCreate(OrganizationContact):
    """
    Alta de una organización (solo admin). Nace `ACTIVE`: las organizaciones
    en prueba las crea el registro público (B10).

    El nombre vacío o de solo espacios no lo rechaza el schema sino el
    service, para responder con el código `INVALID_NAME` que pide la #121
    en lugar del genérico `VALIDATION_ERROR`.
    """

    name: str = Field(
        max_length=NAME_MAX,
        description="Nombre de la organización. No puede estar vacío ni repetirse (sin distinguir mayúsculas).",
        examples=["Hotel Diagonal Mar"],
    )
    first_site: SiteCreate | None = Field(
        default=None,
        description=(
            "Primer edificio del cliente, opcional. Se crea en la misma "
            "operación: o se crean los dos, o ninguno."
        ),
    )


class OrganizationUpdate(OrganizationContact):
    """
    Modificación parcial (solo admin): nombre, contacto y facturación.

    El estado no se cambia aquí: tiene sus propias rutas (`/suspend`,
    `/reactivate`, `/activate`, `/extend-trial`), porque cada cambio de
    estado tiene sus reglas.
    """

    name: str | None = Field(default=None, max_length=NAME_MAX)


class OrganizationResponse(ApiModel):
    """
    Campos según el documento de arquitectura (apartado 5): `id`, `name`,
    `created_at`. La B0 añadió `status` y `trial_ends_at`; la B1, el
    contacto, la facturación y los contadores.

    Los contadores no se guardan: se calculan al responder, con una
    consulta `GROUP BY` por cada uno para toda la página.
    """

    id: UUID
    name: str
    status: OrganizationStatus = Field(
        description="TRIAL (prueba de 7 días), ACTIVE o SUSPENDED."
    )
    trial_ends_at: datetime | None = Field(
        default=None,
        description="Fin de la prueba, en UTC. Solo en organizaciones que están o estuvieron en prueba.",
    )
    city: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    legal_name: str | None = None
    tax_id: str | None = None
    billing_email: str | None = None
    site_count: int = Field(default=0, description="Edificios del cliente.")
    sensor_count: int = Field(default=0, description="Sensores en todos sus edificios.")
    user_count: int = Field(default=0, description="Usuarios de la organización.")
    open_alerts: int = Field(default=0, description="Alertas sin resolver.")
    critical_alerts: int = Field(
        default=0, description="De las alertas sin resolver, cuántas son CRITICAL."
    )
    created_at: datetime = Field(description="Alta de la organización, en UTC.")
