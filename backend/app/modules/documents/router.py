# ROUTER — documents
# Thin HTTP layer: validates schemas → calls the service → answers.
"""
Documents of each building (B11, issue #147):

    POST   /api/documents                 → with a session, multipart (file, site_id, kind)
    GET    /api/documents                 → with a session (each one sees their own)
    GET    /api/documents/{id}/download   → with a session
    DELETE /api/documents/{id}            → with a session; a client does not delete the admin's
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
    **error_response(status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."),
    **error_response(
        status.HTTP_403_FORBIDDEN,
        "Client account without an organization (`FORBIDDEN`).",
    ),
}
_NO_EXISTE = error_response(
    status.HTTP_404_NOT_FOUND,
    "The document does not exist, or is not from your organization (`DOCUMENT_NOT_FOUND`).",
)
# Client writes: with the trial over, read-only (B12).
_SOLO_LECTURA_SI_CADUCA = [Depends(require_trial_not_expired)]


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
    description=(
        "`multipart/form-data` with `file`, `site_id` and `kind`. A client "
        "only uploads to buildings of their organization; an admin, to any.\n\n"
        f"PDF, JPG, PNG or CSV up to {app_settings.MAX_UPLOAD_MB} MB. The "
        "type is checked by the content, not by the extension: an `.exe` "
        "renamed to `.pdf` is rejected."
    ),
    dependencies=_SOLO_LECTURA_SI_CADUCA,
    responses={
        **_NO_AUTORIZADO,
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "Client account without an organization (`FORBIDDEN`), or the trial "
            "is over and the account is read-only (`TRIAL_EXPIRED`).",
        ),
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "The site does not exist, or is not from your organization (`SITE_NOT_FOUND`).",
        ),
        **error_response(
            status.HTTP_413_CONTENT_TOO_LARGE,
            f"The file is over {app_settings.MAX_UPLOAD_MB} MB (`FILE_TOO_LARGE`).",
        ),
        **error_response(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "Empty file (`EMPTY_FILE`), unsupported type "
            "(`UNSUPPORTED_FILE_TYPE`), or a missing field.",
        ),
    },
)
def upload_document(
    service: DocumentSvc,
    user: CurrentUser,
    scope: OrgScope,
    file: Annotated[UploadFile, File(description="The file.")],
    site_id: Annotated[UUID, Form(description="Building it belongs to.")],
    kind: Annotated[DocumentKind, Form(description="Document type.")],
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
    summary="List documents",
    description=(
        "Documents of your organization, newest first. An admin sees those "
        "of every organization. `site_id`, `kind` and `organization_id` "
        "narrow the list."
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
        DocumentKind | None, Query(description="Keeps only those of that type.")
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
    summary="Download a document",
    description=(
        "Returns the file as an attachment, with the name and type it was "
        "stored with. The organization is checked on every download."
    ),
    responses={
        status.HTTP_200_OK: {
            "content": {
                "application/pdf": {},
                "image/jpeg": {},
                "image/png": {},
                "text/csv": {},
            },
            "description": "The file.",
        },
        **_NO_AUTORIZADO,
        **error_response(
            status.HTTP_404_NOT_FOUND,
            "The document does not exist or is not from your organization "
            "(`DOCUMENT_NOT_FOUND`), or its file is missing on disk "
            "(`DOCUMENT_FILE_MISSING`).",
        ),
    },
)
def download_document(
    document_id: UUID, service: DocumentSvc, scope: OrgScope
) -> FileResponse:
    document, path = service.download(document_id, organization_id=scope)
    # `filename` sets `Content-Disposition: attachment`: the browser saves
    # it instead of opening it inside the application.
    return FileResponse(
        path,
        media_type=document.content_type,
        filename=document.filename,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
    description=(
        "Deletes the document and its file. An admin deletes any; a client, "
        "those of their organization not uploaded by an admin."
    ),
    dependencies=_SOLO_LECTURA_SI_CADUCA,
    responses={
        **error_response(status.HTTP_401_UNAUTHORIZED, "No session (`UNAUTHORIZED`)."),
        **error_response(
            status.HTTP_403_FORBIDDEN,
            "Client account without an organization (`FORBIDDEN`), the "
            "document was uploaded by an admin (`DOCUMENT_UPLOADED_BY_ADMIN`), "
            "or the trial is over and the account is read-only (`TRIAL_EXPIRED`).",
        ),
        **_NO_EXISTE,
    },
)
def delete_document(
    document_id: UUID, service: DocumentSvc, user: CurrentUser, scope: OrgScope
) -> Response:
    service.delete(user, document_id, organization_id=scope)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
