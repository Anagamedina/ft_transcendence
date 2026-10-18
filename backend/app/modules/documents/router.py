# ROUTER — documents
# Capa HTTP fina: valida schemas → llama service → responde.
"""
Documentos de cada edificio (B11, issue #147):

    POST   /api/documents                 → con sesión, multipart (file, site_id, kind)
    GET    /api/documents                 → con sesión (cada uno ve lo suyo)
    GET    /api/documents/{id}/download   → con sesión
    DELETE /api/documents/{id}            → con sesión; un cliente no borra lo del admin
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import FileResponse

from app.core.app_config import app_settings
from app.modules.documents.schemas import DocumentResponse
from app.modules.documents.service import DocumentService, get_document_service
from app.shared.dependencies import (
    CurrentUser,
    OrganizationIdFilter,
    OrgScope,
    Pagination,
    SiteIdFilter,
    require_trial_not_expired,
)
from app.shared.enums import DocumentKind
from app.shared.schemas import Page, error_response

router = APIRouter(prefix="/documents", tags=["Documents"])

DocumentSvc = Annotated[DocumentService, Depends(get_document_service)]

_NO_AUTORIZADO = {
    **error_response(status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."),
    **error_response(
        status.HTTP_403_FORBIDDEN,
        "Cuenta de cliente sin organización (`FORBIDDEN`).",
    ),
}
_NO_EXISTE = error_response(
    status.HTTP_404_NOT_FOUND,
    "El documento no existe, o no es de tu organización (`DOCUMENT_NOT_FOUND`).",
)
# Escrituras de cliente: con la prueba vencida, solo lectura (B12).
_SOLO_LECTURA_SI_CADUCA = [Depends(require_trial_not_expired)]


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir un documento",
    description=(
        "`multipart/form-data` con `file`, `site_id` y `kind`. Un cliente "
        "sube solo a edificios de su organización; un admin, a cualquiera.\n\n"
        f"PDF, JPG, PNG o CSV de hasta {app_settings.MAX_UPLOAD_MB} MB. El "
        "tipo se comprueba por el contenido, no por la extensión: un `.exe` "
        "renombrado a `.pdf` se rechaza."
    ),
    dependencies=_SOLO_LECTURA_SI_CADUCA,
    responses={
        **_NO_AUTORIZADO,
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "Cuenta de cliente sin organización (`FORBIDDEN`), o la prueba ha "
            "vencido y la cuenta es de solo lectura (`TRIAL_EXPIRED`).",
        ),
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "El site no existe, o no es de tu organización (`SITE_NOT_FOUND`).",
        ),
        **error_response(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"El archivo pasa de {app_settings.MAX_UPLOAD_MB} MB (`FILE_TOO_LARGE`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Archivo vacío (`EMPTY_FILE`), de un tipo no admitido "
            "(`UNSUPPORTED_FILE_TYPE`), o falta algún campo.",
        ),
    },
)
def upload_document(
    service: DocumentSvc,
    user: CurrentUser,
    scope: OrgScope,
    file: Annotated[UploadFile, File(description="El archivo.")],
    site_id: Annotated[UUID, Form(description="Edificio al que pertenece.")],
    kind: Annotated[DocumentKind, Form(description="Tipo de documento.")],
) -> DocumentResponse:
    return service.upload(
        user=user,
        organization_id=scope,
        site_id=site_id,
        kind=kind,
        filename=file.filename,
        source=file.file,
    )


@router.get(
    "",
    response_model=Page[DocumentResponse],
    summary="Listar documentos",
    description=(
        "Documentos de tu organización, del más nuevo al más antiguo. Un "
        "admin ve los de todas. `site_id`, `kind` y `organization_id` "
        "estrechan la lista."
    ),
    responses={**_NO_AUTORIZADO},
)
def list_documents(
    service: DocumentSvc,
    user: CurrentUser,
    scope: OrgScope,
    pagination: Pagination,
    site_id: SiteIdFilter = None,
    kind: Annotated[
        DocumentKind | None, Query(description="Deja solo los de ese tipo.")
    ] = None,
    organization_id: OrganizationIdFilter = None,
) -> Page[DocumentResponse]:
    return service.list(
        user=user,
        organization_id=scope,
        offset=pagination.offset,
        limit=pagination.limit,
        site_id=site_id,
        kind=kind,
        organization_filter=organization_id,
    )


@router.get(
    "/{document_id}/download",
    response_class=FileResponse,
    summary="Descargar un documento",
    description=(
        "Devuelve el archivo como adjunto, con el nombre y el tipo con que "
        "se guardó. Se comprueba la organización en cada descarga."
    ),
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/pdf": {},
                "image/jpeg": {},
                "image/png": {},
                "text/csv": {},
            },
            "description": "El archivo.",
        },
        **_NO_AUTORIZADO,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "El documento no existe o no es de tu organización "
            "(`DOCUMENT_NOT_FOUND`), o su archivo falta en el disco "
            "(`DOCUMENT_FILE_MISSING`).",
        ),
    },
)
def download_document(
    document_id: UUID, service: DocumentSvc, scope: OrgScope
) -> FileResponse:
    document, path = service.download(document_id, organization_id=scope)
    # `filename` pone `Content-Disposition: attachment`: el navegador lo
    # guarda en vez de abrirlo dentro de la aplicación.
    return FileResponse(
        path,
        media_type=document.content_type,
        filename=document.filename,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar un documento",
    description=(
        "Borra el documento y su archivo. Un admin borra cualquiera; un "
        "cliente, los de su organización que no haya subido un admin."
    ),
    dependencies=_SOLO_LECTURA_SI_CADUCA,
    responses={
        **error_response(status.HTTP_401_UNAUTHORIZED, "No hay sesión (`UNAUTHORIZED`)."),
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "Cuenta de cliente sin organización (`FORBIDDEN`), el documento "
            "lo subió un admin (`DOCUMENT_UPLOADED_BY_ADMIN`), o la prueba ha "
            "vencido y la cuenta es de solo lectura (`TRIAL_EXPIRED`).",
        ),
        **_NO_EXISTE,
    },
)
def delete_document(
    document_id: UUID, service: DocumentSvc, user: CurrentUser, scope: OrgScope
) -> Response:
    service.delete(user, document_id, organization_id=scope)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
