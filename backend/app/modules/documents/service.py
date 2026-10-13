# SERVICE — documents
# Reglas de negocio y orquestación. No hablar HTTP aquí.
"""
Documentos de cada edificio (B11, issue #147).

Reglas:

- **Alcance.** Un cliente sube, lista, descarga y borra solo en los
  edificios de su organización; un admin, en todos. Un documento o un
  edificio de otra organización responde 404, igual que uno que no existe.
- **El cliente no borra lo que sube un admin** (403
  `DOCUMENT_UPLOADED_BY_ADMIN`). Si el autor ya no existe no se sabe quién
  lo subió, así que tampoco: lo borra un admin.
- **El tipo se decide por el contenido**, nunca por la extensión ni por el
  `Content-Type` que manda el navegador: PDF, JPG y PNG por su firma, CSV
  por ser texto. Es lo que se guarda en `content_type` y con lo que se
  sirve la descarga.
- **Hasta `MAX_UPLOAD_MB`** (413 `FILE_TOO_LARGE`). El gateway ya corta
  antes, pero el backend no se fía de que haya un gateway delante.

Archivo y fila no comparten transacción: el archivo se escribe antes del
INSERT y se borra si el INSERT falla; al borrar, primero se borra la fila y
después del commit el archivo. Así nunca queda una fila sin archivo; como
mucho, un archivo huérfano si el proceso muere justo en medio.
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

# Firmas de los formatos binarios admitidos (los primeros bytes del archivo).
_FIRMAS = (
    (b"%PDF-", "application/pdf"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"\x89PNG\r\n\x1a\n", "image/png"),
)
# Un CSV es texto: fuera de tabuladores y saltos de línea, ningún carácter
# de control. Un binario cualquiera (un .exe renombrado a .csv) los tiene.
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0e-\x1f\x7f]")

FILENAME_MAX = 255


class DocumentService:
    def __init__(self, db: Session, root: str | Path | None = None) -> None:
        self.db = db
        self.documents = DocumentRepository(db)
        self.sites = SiteRepository(db)
        # Carpeta de los archivos; los tests la cambian por una temporal.
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
        # El edificio tiene que ser visible para quien sube; la organización
        # del documento sale de él, nunca de la petición.
        if self.sites.get_by_id(site_id, organization_id) is None:
            raise NotFoundError("El site indicado no existe.", code="SITE_NOT_FOUND")

        size = _size(source)
        content_type = detect_content_type(source)

        # Lo genera el backend: dos «plano.pdf» no chocan y el nombre del
        # usuario nunca llega a ser una ruta del disco.
        storage_key = uuid.uuid4().hex
        storage.save_file(source, storage_key, root=self.root)
        try:
            with transaction(self.db):
                # Bloquea el edificio como su borrado (B2): si se está
                # borrando a la vez, uno espera al otro y no queda un
                # documento colgando de un edificio que ya no existe.
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
        """El documento y su archivo, si quien pregunta puede verlo."""
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
        # Después del commit: si la transacción falla, el archivo sigue ahí.
        storage.delete_files([storage_key], root=self.root)

    def _visible(self, document_id: UUID, organization_id: UUID | None) -> DocumentRow:
        fila = self.documents.get(document_id, organization_id)
        if fila is None:
            raise NotFoundError(
                "El documento indicado no existe.", code="DOCUMENT_NOT_FOUND"
            )
        return fila


def _size(source: BinaryIO) -> int:
    """Tamaño del archivo subido, o 413 si pasa de `MAX_UPLOAD_MB`."""
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
    El tipo del archivo según su contenido, o 422 `UNSUPPORTED_FILE_TYPE`.

    PDF, JPG y PNG se reconocen por su firma. Lo demás solo se acepta como
    CSV si es texto: UTF-8 (con o sin BOM) o, si no lo es, Windows-1252,
    que es como guarda Excel en español.
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
    El nombre que se guarda y se propone al descargar: sin carpetas (un
    navegador antiguo manda `C:\\Users\\...\\plano.pdf`), sin caracteres de
    control y de 255 caracteres como mucho, conservando la extensión.
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
    """El admin borra cualquiera; el cliente, solo los que subió un cliente."""
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
    """Proveedor del service para `Depends`."""
    return DocumentService(db)
