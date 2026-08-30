# SCHEMAS — organizations
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de organizaciones (issue #23).

La organización es el cliente de AquaGuard: una comunidad, un municipio o
una empresa. Es además la **unidad de aislamiento** de todo el sistema.

    organization → sites → sensors → readings → alerts

Todo cuelga de ella, y esa cadena es lo que permite responder a la
pregunta "¿puede este usuario ver esta lectura?" subiendo por las
relaciones hasta la organización. El aislamiento efectivo se implementa en
la issue #27; el contrato ya lo refleja exponiendo `organization_id` en
los recursos que dependen de él.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.shared.schemas import ApiModel, ApiRequest


class OrganizationCreate(ApiRequest):
    name: str = Field(
        min_length=1,
        max_length=120,
        description="Nombre de la organización.",
        examples=["Hotel Group"],
    )


class OrganizationResponse(ApiModel):
    """
    Campos según el documento de arquitectura (apartado 5):
    `id`, `name`, `created_at`. Nada más — el CRUD de organizaciones
    pertenece al nivel Intermedio de la API (apartado 9.2).
    """

    id: UUID
    name: str
    created_at: datetime = Field(description="Alta de la organización, en UTC.")
