# SCHEMAS — documents
# Pydantic request/response (OpenAPI contract). Never return a raw ORM model.
"""
Contract of the documents of a building (B11, issue #147).

The upload is `multipart/form-data` (`file`, `site_id`, `kind`), so it has
no input schema: FastAPI documents the form fields from the endpoint
signature.
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
    site_name: str = Field(description="Building name, for the list.")
    kind: DocumentKind
    filename: str = Field(
        description="Original file name, the one offered on download.",
        examples=["plano-planta-baja.pdf"],
    )
    content_type: str = Field(
        description=(
            "Type detected by the server from the content, not from the "
            "extension: `application/pdf`, `image/jpeg`, `image/png` or `text/csv`."
        ),
        examples=["application/pdf"],
    )
    size: int = Field(description="Size in bytes.", examples=[184320])
    uploaded_by: UUID | None = Field(
        description="Who uploaded it. `null` if that user no longer exists."
    )
    can_delete: bool = Field(
        description=(
            "Whether the caller can delete it. A client does not delete what "
            "an admin uploaded."
        )
    )
    created_at: datetime
