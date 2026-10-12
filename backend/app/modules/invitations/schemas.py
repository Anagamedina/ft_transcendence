# SCHEMAS — invitations
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de las invitaciones (B4, issue #141).

Se publica antes que las rutas, como en la #23, para que el frontend
(F6 de Florinda y F11 de Eduardo) monte sus pantallas con mocks. Las rutas
previstas:

    POST   /api/invitations                       admin  → InvitationSentResponse (201)
    GET    /api/invitations                       admin  → Page[InvitationResponse]
    DELETE /api/invitations/{id}                  admin  → 204 (revocar)
    POST   /api/invitations/{id}/resend           admin  → InvitationSentResponse
    GET    /api/invitations/by-code/{code}        público → InvitationPublicResponse
    POST   /api/invitations/by-code/{code}/accept público → SessionResponse (201)

Las dos rutas públicas empiezan por `/api/invitations/by-code/` a
propósito: es lo que el gateway limita por IP (I11, PR #199).

**El código solo sale una vez**: en la respuesta del alta y en la del
reenvío. En la base se guarda su hash (D3), así que después no se puede
volver a enseñar; por eso `InvitationResponse` no lo lleva.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import EmailStr, Field

from app.shared.enums import InvitationStatus
from app.shared.schemas import ApiModel, ApiRequest


class InvitationCreate(ApiRequest):
    """Invitar a un email a una organización que ya existe (admin)."""

    email: EmailStr = Field(
        description="A quién se invita. Se guarda en minúsculas.",
        examples=["nuevo.gestor@hotelmar.com"],
    )
    organization_id: UUID = Field(
        description="Organización a la que se unirá al aceptar.",
        examples=["11111111-1111-4111-8111-111111111111"],
    )


class InvitationResponse(ApiModel):
    """Una invitación en la lista del admin. Sin el código."""

    id: UUID
    organization_id: UUID
    organization_name: str = Field(examples=["Hotel Mar"])
    email: EmailStr = Field(examples=["nuevo.gestor@hotelmar.com"])
    status: InvitationStatus = Field(
        description="Calculado a partir de las fechas: ver `InvitationStatus`.",
        examples=["PENDING"],
    )
    expires_at: datetime = Field(
        description="Caduca a los `INVITATION_TTL_DAYS` días (7 por defecto), en UTC."
    )
    accepted_at: datetime | None = None
    revoked_at: datetime | None = None
    created_by_name: str | None = Field(
        default=None,
        description="Quién la envió. Nulo si ese usuario ya no existe.",
        examples=["Ana Medina"],
    )
    created_at: datetime


class InvitationSentResponse(InvitationResponse):
    """
    Respuesta del alta y del reenvío: la invitación más el código y el
    enlace. **Es la única vez que se ven**; el admin los copia o se envían
    por email. Reenviar genera un código nuevo y el anterior deja de valer.
    """

    code: str = Field(
        description="Código de un solo uso. No se puede volver a consultar.",
        examples=["k3Vq9mZt2xR8"],
    )
    url: str = Field(
        description=(
            "Enlace para aceptar: `PUBLIC_BASE_URL` + `/registro?invitacion={code}`, "
            "la ruta que lee la F6."
        ),
        examples=["https://localhost/registro?invitacion=k3Vq9mZt2xR8"],
    )


class InvitationPublicResponse(ApiModel):
    """
    Lo que ve quien abre el enlace, sin sesión: lo justo para el
    formulario de aceptar. Una invitación caducada responde 410
    `INVITATION_EXPIRED`; una aceptada, revocada o inexistente, 404
    `INVITATION_NOT_FOUND`.
    """

    organization_name: str = Field(examples=["Hotel Mar"])
    email: EmailStr = Field(examples=["nuevo.gestor@hotelmar.com"])
    expires_at: datetime


class InvitationAccept(ApiRequest):
    """
    Aceptar la invitación: crea el usuario `client` en la organización y
    abre la sesión, como el registro. El email no se elige: es el de la
    invitación.
    """

    name: str = Field(min_length=1, max_length=120, examples=["Laura Puig"])
    password: str = Field(
        max_length=128,
        description=(
            "Misma regla que el registro (B10): al menos 12 caracteres, que "
            "no sea común ni contenga el email. Si no, 422 `WEAK_PASSWORD`."
        ),
        examples=["agua-que-no-se-escapa"],
    )
    accept_terms: bool = Field(
        description="Tiene que ser `true`. Si no, 422 `TERMS_NOT_ACCEPTED`.",
        examples=[True],
    )
