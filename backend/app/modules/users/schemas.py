# SCHEMAS — users
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de usuarios (issue #23).

El punto importante de este archivo es la separación entre lo que entra y
lo que sale:

    UserCreate   → password    (entra, nunca sale)
    UserResponse → sin password ni hash

Es tentador declarar un único `User` y reutilizarlo en las dos
direcciones. No se hace porque el día que el modelo gane un campo
`password_hash` o `reset_token`, ese campo aparecería solo en la respuesta
de la API. Con schemas separados eso no puede ocurrir: `UserResponse`
únicamente copia los campos que declara.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import EmailStr, Field

from app.shared.enums import (
    BillingPeriod,
    BuildingType,
    OrganizationStatus,
    SubscriptionPlan,
)
from app.shared.schemas import ApiModel, ApiRequest, Password


class UserRole(str, Enum):
    """
    Rol dentro de la aplicación.

    Hereda de `str` para que serialice como `"admin"` y no como
    `"UserRole.ADMIN"`, y para poder compararlo con una cadena sin
    convertir. En OpenAPI aparece como un enum de strings, que es lo que
    el frontend necesita para pintar el selector.

    - `admin`  → gestiona organizaciones, sites y sensores.
    - `client` → solo ve los datos de su propia organización.
    """

    ADMIN = "admin"
    CLIENT = "client"


class UserBase(ApiRequest):
    email: EmailStr = Field(
        description="Email del usuario. Único en todo el sistema.",
        examples=["admin@hotel.com"],
    )
    name: str = Field(
        min_length=1,
        max_length=120,
        description="Nombre para mostrar.",
        examples=["Ana Medina"],
    )



class UserCreate(UserBase):
    """Alta de usuario. La contraseña entra por aquí y no sale nunca."""

    password: str = Field(
        min_length=8,
        max_length=128,
        description=(
            "Contraseña en claro. Se envía solo por HTTPS y se guarda "
            "hasheada (issue #26). El mínimo de 8 se valida aquí para no "
            "llegar al service con algo que ya se sabe inválido."
        ),
        examples=["una-contrasena-larga"],
    )


class UserUpdate(ApiRequest):
    """
    Modificación parcial. Todos los campos son opcionales.

    `None` y "campo ausente" significan cosas distintas: para saber cuáles
    tocó el cliente hay que usar `model_dump(exclude_unset=True)`, no
    `exclude_none`.
    """

    name: str | None = Field(default=None, min_length=1, max_length=120)
    role: UserRole | None = None
    # B6 (#141): mover o añadir un usuario a una organización. Un `client`
    # siempre necesita una (CHECK `ck_users_client_has_organization`). El
    # email no se edita: no está aquí, y `extra="forbid"` lo rechaza.
    organization_id: UUID | None = Field(
        default=None,
        description="Organización del usuario. Obligatoria si queda como `client`.",
    )


class UserResponse(ApiModel):
    """
    Usuario tal y como lo ve el cliente.

    Campos según el modelo de dominio del documento de arquitectura
    (apartado 5): `id`, `organization_id`, `name`, `email`, `role`,
    `created_at`. `password_hash` existe en la tabla y NO aparece aquí:
    es justamente lo que garantiza la separación entrada/salida.
    """

    id: UUID = Field(description="Identificador del usuario.")
    email: EmailStr
    name: str
    role: UserRole
    organization_id: UUID | None = Field(
        default=None,
        description=(
            "Organización a la que pertenece. Nulo para un admin global, "
            "que no está atado a ninguna."
        ),
    )
    created_at: datetime = Field(description="Alta del usuario, en UTC.")


# ---------------------------------------------------------
# CONTRATO DE LA B6 Y LA B8 (#141, #144)
# ---------------------------------------------------------
# Se publican antes que las rutas, como en la #23, para que el frontend
# (F11 y F13 de Eduardo y Lylia) monte sus pantallas con mocks.
#
# B6 — usuarios (admin):
#   GET    /api/users?organization_id=&q=&active=  → Page[UserAdminResponse]
#   GET    /api/users/{id}                         → UserAdminResponse
#   PATCH  /api/users/{id}                         → UserAdminResponse (UserUpdate)
#   POST   /api/users/{id}/deactivate              → UserAdminResponse
#   POST   /api/users/{id}/activate                → UserAdminResponse
#   DELETE /api/users/{id}                         → 204
#
# B8 — Mi cuenta (cualquiera con sesión):
#   GET    /api/me                → MeResponse
#   PATCH  /api/me                → MeResponse (MeUpdate)
#   POST   /api/me/password       → MessageResponse (PasswordChange)
class UserAdminResponse(UserResponse):
    """Un usuario en la gestión de usuarios del admin (B6)."""

    organization_name: str | None = Field(
        default=None, description="Nombre de su organización.", examples=["Hotel Mar"]
    )
    is_active: bool = Field(
        default=True,
        description=(
            "`false` si un admin lo ha desactivado: no puede entrar (403 "
            "`ACCOUNT_DISABLED`)."
        ),
    )
    last_login_at: datetime | None = Field(
        default=None, description="Último login, en UTC. Nulo si nunca ha entrado."
    )


class OrganizationSummary(ApiModel):
    """La organización de quien tiene la sesión, para Mi cuenta (B8)."""

    id: UUID
    name: str = Field(examples=["Hotel Mar"])
    status: OrganizationStatus = Field(examples=["TRIAL"])
    trial_ends_at: datetime | None = Field(
        default=None, description="Fin de la prueba, en UTC. Nulo si no está en prueba."
    )


class MeResponse(ApiModel):
    """
    Respuesta de `GET /api/me` desde la B8. Mantiene `user` donde estaba
    (el frontend ya lo lee así) y añade lo de Mi cuenta.
    """

    user: UserResponse
    organization: OrganizationSummary | None = Field(
        default=None, description="Nula para un admin sin organización."
    )
    last_login_at: datetime | None = None
    terms_version: str | None = Field(
        default=None,
        description="Versión de los términos que aceptó. Nula en cuentas anteriores a la B10.",
        examples=["2026-10"],
    )
    terms_accepted_at: datetime | None = None
    deletion_requested_at: datetime | None = Field(
        default=None,
        description="Cuándo pidió la baja (B15), en UTC. Nulo si no la ha pedido.",
    )


class CurrentSessionResponse(ApiModel):
    """Respuesta de `GET /api/me/session`: el usuario, o `null` sin sesión."""

    user: MeResponse | None = Field(
        default=None, description="Lo mismo que `GET /api/me`, o nulo si no hay sesión."
    )


class MeUpdate(ApiRequest):
    """Lo que cada uno puede cambiar de su cuenta (B8). El email no."""

    name: str = Field(min_length=1, max_length=120, examples=["Ana Medina"])


class PasswordChange(ApiRequest):
    """
    Cambiar la propia contraseña (B8). Si `current_password` no coincide,
    422 `WRONG_PASSWORD` (no 401: la sesión sigue siendo válida, y un 401
    haría que el frontend la cerrara); si la nueva no cumple la regla de
    la B10, 422 `WEAK_PASSWORD`. Las demás sesiones abiertas no se cierran (necesitaría
    una columna que no existe).
    """

    current_password: str = Field(min_length=1, max_length=128)
    new_password: Password = Field(
        max_length=128,
        description="Misma regla que el registro (B10): al menos 12 caracteres, no común, sin el email.",
        examples=["agua-que-no-se-escapa"],
    )


# ---------------------------------------------------------
# B15 — EXPORTAR MIS DATOS Y PEDIR LA BAJA (#149)
# ---------------------------------------------------------
#   GET  /api/me/export            → MyDataExport (se descarga como .json)
#   POST /api/me/deletion-request  → DeletionRequestResponse
#
# Los schemas de la exportación son propios, no `SiteResponse` ni
# `OrganizationResponse`: llevan solo lo que está guardado (sin contadores
# ni estados calculados) y no cambian si cambian las pantallas.
class AccountExport(ApiModel):
    """La cuenta de quien exporta. Sin `password_hash`, como `UserResponse`."""

    id: UUID
    email: EmailStr
    name: str
    role: UserRole
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None
    terms_version: str | None = Field(
        default=None,
        description="Versión de los términos que aceptó (B10). Nula en cuentas anteriores.",
        examples=["2026-10"],
    )
    terms_accepted_at: datetime | None = None
    deletion_requested_at: datetime | None = None


class OrganizationExport(ApiModel):
    """La organización tal y como está guardada. El IBAN, solo enmascarado."""

    id: UUID
    name: str
    status: OrganizationStatus
    trial_ends_at: datetime | None = None
    city: str | None = None
    contact_email: str | None = None
    phone: str | None = None
    legal_name: str | None = None
    tax_id: str | None = None
    billing_email: str | None = None
    billing_address: str | None = None
    postal_code: str | None = None
    plan: SubscriptionPlan | None = None
    billing_period: BillingPeriod | None = None
    contracted_sites: int | None = None
    contracted_sensors: int | None = None
    monthly_price_eur: int | None = None
    subscribed_at: datetime | None = None
    iban_masked: str | None = None
    sepa_accepted_at: datetime | None = None
    created_at: datetime


class SiteExport(ApiModel):
    """Un edificio de la organización, con lo que está guardado."""

    id: UUID
    name: str
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    district: str | None = None
    floors: int
    basements: int
    building_type: BuildingType
    created_at: datetime


class MyDataExport(ApiModel):
    """
    Todo lo que AquaGuard guarda de la cuenta (B15): la cuenta, su
    organización y sus edificios. Un admin sin organización recibe
    `organization` nula y `sites` vacía, no los edificios de todos.
    """

    exported_at: datetime = Field(description="Cuándo se generó, en UTC.")
    current_terms_version: str = Field(
        description=(
            "Versión de los términos vigente. Si no coincide con "
            "`account.terms_version`, la cuenta aceptó unos anteriores."
        ),
        examples=["2026-10"],
    )
    account: AccountExport
    organization: OrganizationExport | None = None
    sites: list[SiteExport] = Field(default_factory=list)


class DeletionRequestResponse(ApiModel):
    """Petición de baja registrada (B15). Nada se borra todavía."""

    deletion_requested_at: datetime = Field(
        description="Cuándo se pidió por primera vez, en UTC. Repetir la petición no la cambia."
    )
    message: str = Field(
        examples=["Hemos registrado tu petición de baja. Un administrador la tramitará."]
    )
