# SERVICE — documents
# Business rules and orchestration. No HTTP here.
"""
Documents of each building (B11, issue #147).

Rules:

- **Scope.** A client uploads, lists, downloads and deletes only in the
  buildings of their organization; an admin, in all of them. A document
  or a building from another organization answers 404, like one that does
  not exist.
- **The client does not delete what an admin uploads** (403
  `DOCUMENT_UPLOADED_BY_ADMIN`). If the author no longer exists, nobody
  knows who uploaded it, so neither: an admin deletes it.
- **The type is decided by the content**, never by the extension nor by
  the `Content-Type` the browser sends: PDF, JPG and PNG by their
  signature, CSV by being text. It is what is stored in `content_type` and
  what the download is served with.
- **Up to `MAX_UPLOAD_MB`** (413 `FILE_TOO_LARGE`). The gateway already
  cuts earlier, but the backend does not trust that a gateway is in front.

File and row do not share a transaction: the file is written before the
INSERT and deleted if the INSERT fails; on delete, the row goes first and
the file after the commit. So there is never a row without a file; at
most, an orphan file if the process dies right in between.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.app_config import app_settings
from app.core.database import transaction
from app.core.exceptions import (
    DomainValidationError,
    ForbiddenError,
    NotFoundError,
    PayloadTooLargeError,
)
from app.modules.documents import storage
from app.modules.documents.model import Document
from app.modules.documents.repository import DocumentRepository, DocumentRow
from app.modules.documents.schemas import DocumentResponse
from app.modules.sites.repository import SiteRepository
from app.modules.users.model import User
from app.shared.dependencies import DbSession
from app.shared.enums import DocumentKind
from app.shared.schemas import Page

# Signatures of the accepted binary formats (the first bytes of the file).
_FIRMAS = (
    (b"%PDF-", "application/pdf"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
)
# A CSV is text: apart from tabs and line breaks, no control characters. Any
# binary (an .exe renamed to .csv) has them.
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0e-\x1f\x7f]")

FILENAME_MAX = 255


class DocumentService:
    def __init__(self, db: Session, root: str | Path | None = None) -> None:
        self.db = db
        self.documents = DocumentRepository(db)
        self.sites = SiteRepository(db)
        # Folder of the files; the tests replace it with a temporary one.
        self.root = root

    def list(
        self,
        user: User,
        organization_id: UUID | None,
        offset: int,
        limit: int,
        site_id: UUID | None = None,
        kind: DocumentKind | None = None,
        organization_filter: UUID | None = None,
    ) -> Page[DocumentResponse]:
        filas, total = self.documents.list(
            organization_id=organization_id,
            offset=offset,
            limit=limit,
            site_id=site_id,
            kind=None if kind is None else kind.value,
            organization_filter=organization_filter,
        )
        return Page[DocumentResponse](
            items=[_to_response(f, user) for f in filas],
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    def upload(
        self,
        user: User,
        organization_id: UUID | None,
        site_id: UUID,
        kind: DocumentKind,
        filename: str | None,
        source: BinaryIO,
    ) -> DocumentResponse:
        # The building must be visible to the uploader; the organization of
        # the document comes from it, never from the request.
        if self.sites.get_by_id(site_id, organization_id) is None:
            raise NotFoundError("El site indicado no existe.", code="SITE_NOT_FOUND")

        size = _size(source)
        content_type = detect_content_type(source)

        # The backend generates it: two "plano.pdf" do not clash and the
        # user's file name never becomes a path on disk.
        storage_key = uuid.uuid4().hex
        storage.save_file(source, storage_key, root=self.root)
        try:
            with transaction(self.db):
                # Locks the building like its deletion does (B2): if it is
                # being deleted at the same time, one waits for the other
                # and no document is left hanging from a building that no
                # longer exists.
                site = self.sites.get_for_update(site_id)
                if site is None:
                    raise NotFoundError(
                        "El site indicado no existe.", code="SITE_NOT_FOUND"
                    )
                document = self.documents.create(
                    organization_id=site.organization_id,
                    site_id=site.id,
                    kind=kind.value,
                    filename=clean_filename(filename),
                    content_type=content_type,
                    size=size,
                    storage_key=storage_key,
                    uploaded_by=user.id,
                )
        except BaseException:
            storage.delete_files([storage_key], root=self.root)
            raise
        return _to_response(DocumentRow(document, site.name, user.role), user)

    def download(
        self, document_id: UUID, organization_id: UUID | None
    ) -> tuple[Document, Path]:
        """The document and its file, if the caller can see it."""
        fila = self._visible(document_id, organization_id)
        path = storage.file_path(fila.document.storage_key, root=self.root)
        if path is None:
            raise NotFoundError(
                "El archivo de este documento no está disponible.",
                code="DOCUMENT_FILE_MISSING",
            )
        return fila.document, path

    def delete(self, user: User, document_id: UUID, organization_id: UUID | None) -> None:
        with transaction(self.db):
            fila = self._visible(document_id, organization_id)
            if not _can_delete(user, fila.uploader_role):
                raise ForbiddenError(
                    "Este documento lo subió AquaGuard y solo AquaGuard puede borrarlo.",
                    code="DOCUMENT_UPLOADED_BY_ADMIN",
                )
            storage_key = fila.document.storage_key
            self.documents.delete(fila.document)
        # After the commit: if the transaction fails, the file is still there.
        storage.delete_files([storage_key], root=self.root)

    def _visible(self, document_id: UUID, organization_id: UUID | None) -> DocumentRow:
        fila = self.documents.get(document_id, organization_id)
        if fila is None:
            raise NotFoundError(
                "El documento indicado no existe.", code="DOCUMENT_NOT_FOUND"
            )
        return fila


def _size(source: BinaryIO) -> int:
    """Size of the uploaded file, or 413 if it is over `MAX_UPLOAD_MB`."""
    source.seek(0, 2)
    size = source.tell()
    source.seek(0)
    if size > app_settings.MAX_UPLOAD_MB * 1024 * 1024:
        raise PayloadTooLargeError(
            f"El archivo pasa de {app_settings.MAX_UPLOAD_MB} MB.",
            code="FILE_TOO_LARGE",
        )
    if size == 0:
        raise DomainValidationError("El archivo está vacío.", code="EMPTY_FILE")
    return size


def detect_content_type(source: BinaryIO) -> str:
    """
    The file type according to its content, or 422 `UNSUPPORTED_FILE_TYPE`.

    PDF, JPG and PNG are recognized by their signature. Anything else is
    only accepted as CSV if it is text: UTF-8 (with or without BOM) or,
    otherwise, Windows-1252, which is how Excel saves in Spanish.
    """
    source.seek(0)
    inicio = source.read(16)
    for firma, tipo in _FIRMAS:
        if inicio.startswith(firma):
            source.seek(0)
            return tipo

    source.seek(0)
    datos = source.read()
    source.seek(0)
    if _es_texto(datos):
        return "text/csv"
    raise DomainValidationError(
        "Solo se admiten archivos PDF, JPG, PNG o CSV.",
        code="UNSUPPORTED_FILE_TYPE",
    )


def _es_texto(datos: bytes) -> bool:
    for codificacion in ("utf-8-sig", "cp1252"):
        try:
            texto = datos.decode(codificacion)
        except UnicodeDecodeError:
            continue
        return _CONTROL.search(texto) is None
    return False


def clean_filename(filename: str | None) -> str:
    """
    The name stored and offered on download: without folders (an old
    browser sends `C:\\Users\\...\\plano.pdf`), without control characters
    and 255 characters at most, keeping the extension.
    """
    nombre = re.split(r"[\\/]", filename or "")[-1]
    nombre = _CONTROL.sub("", nombre).strip()
    if not nombre or nombre in (".", ".."):
        return "documento"
    if len(nombre) > FILENAME_MAX:
        base, punto, ext = nombre.rpartition(".")
        if punto and 0 < len(ext) < 16:
            nombre = base[: FILENAME_MAX - len(ext) - 1] + "." + ext
        else:
            nombre = nombre[:FILENAME_MAX]
    return nombre


def _can_delete(user: User, uploader_role: str | None) -> bool:
    """The admin deletes any; the client, only those a client uploaded."""
    return user.role == "admin" or uploader_role == "client"


def _to_response(fila: DocumentRow, user: User) -> DocumentResponse:
    d = fila.document
    return DocumentResponse(
        id=d.id,
        organization_id=d.organization_id,
        site_id=d.site_id,
        site_name=fila.site_name,
        kind=d.kind,
        filename=d.filename,
        content_type=d.content_type,
        size=d.size,
        uploaded_by=d.uploaded_by,
        can_delete=_can_delete(user, fila.uploader_role),
        created_at=d.created_at,
    )


def get_document_service(db: DbSession) -> DocumentService:
    """Service provider for `Depends`."""
    return DocumentService(db)
