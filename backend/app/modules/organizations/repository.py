"""Persistence queries for organizations."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.organizations.model import Organization


class OrganizationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_id(self, organization_id: UUID) -> Organization | None:
        return self.db.get(Organization, organization_id)
