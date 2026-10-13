# SCHEMAS — documents
# Pydantic request/response (contrato OpenAPI). No devolver model ORM crudo.
"""
Contrato de los documentos de un edificio (B11, issue #147).

La subida es `multipart/form-data` (`file`, `site_id`, `kind`), así que no
tiene schema de entrada: FastAPI documenta los campos del formulario a
partir de la firma del endpoint.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.shared.enums import DocumentKind
from app.shared.schemas import ApiModel


class DocumentResponse(ApiModel):
    id: UUID
    organization_id: UUID
    site_id: UUID
    site_name: str = Field(description="Nombre del edificio, para la lista.")
    kind: DocumentKind
    filename: str = Field(
        description="Nombre original del archivo, el que se propone al descargarlo.",
        examples=["plano-planta-baja.pdf"],
    )
    content_type: str = Field(
        description=(
            "Tipo detectado por el servidor a partir del contenido, no de la "
            "extensión: `application/pdf`, `image/jpeg`, `image/png` o `text/csv`."
        ),
        examples=["application/pdf"],
    )
    size: int = Field(description="Tamaño en bytes.", examples=[184320])
    uploaded_by: UUID | None = Field(
        description="Quién lo subió. `null` si ese usuario ya no existe."
    )
    can_delete: bool = Field(
        description=(
            "Si quien pregunta puede borrarlo. Un cliente no borra lo que "
            "subió un admin."
        )
    )
    created_at: datetime
