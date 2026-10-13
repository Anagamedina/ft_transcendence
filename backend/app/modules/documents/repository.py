# REPOSITORY — documents
# Acceso a datos (SQLAlchemy queries). Filtrar siempre por organización.
"""
Consultas de documentos (B11, issue #147).

`organization_id=None` significa TODAS las organizaciones (admin), como en
el resto de repositories. Lo decide `get_org_scope`.

Cada fila sale con el nombre de su edificio y el rol de quien la subió:
la respuesta los necesita (`site_name`, `can_delete`) y así no hace falta
una consulta por documento.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.modules.documents.model import Document
from app.modules.sites.model import Site
from app.modules.users.model import User


@dataclass(frozen=True)
class DocumentRow:
    document: Document
    site_name: str
    uploader_role: str | None


class DocumentRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _query(self, organization_id: UUID | None) -> Select:
        query = (
            select(Document, Site.name, User.role)
            .join(Site, Site.id == Document.site_id)
            .outerjoin(User, User.id == Document.uploaded_by)
        )
        if organization_id is not None:
            query = query.where(Document.organization_id == organization_id)
        return query

    def list(
        self,
        organization_id: UUID | None,
        offset: int = 0,
        limit: int = 100,
        site_id: UUID | None = None,
        kind: str | None = None,
        organization_filter: UUID | None = None,
    ) -> tuple[list[DocumentRow], int]:
        """
        `organization_id` es el alcance de la sesión; el resto, filtros que
        lo estrechan. Del más nuevo al más antiguo (índice
        `ix_documents_site_created_at`).
        """
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        query = self._query(organization_id)
        if organization_filter is not None:
            query = query.where(Document.organization_id == organization_filter)
        if site_id is not None:
            query = query.where(Document.site_id == site_id)
        if kind is not None:
            query = query.where(Document.kind == kind)

        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        filas = self.db.execute(
            query.order_by(Document.created_at.desc(), Document.id.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return [DocumentRow(*f) for f in filas], int(total or 0)

    def get(self, document_id: UUID, organization_id: UUID | None) -> DocumentRow | None:
        fila = self.db.execute(
            self._query(organization_id).where(Document.id == document_id)
        ).first()
        return DocumentRow(*fila) if fila else None

    def create(self, **campos) -> Document:
        document = Document(**campos)
        self.db.add(document)
        self.db.flush()
        self.db.refresh(document)
        return document

    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.flush()
