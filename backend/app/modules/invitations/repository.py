"""Persistence queries for invitations (B4, issue #141)."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.invitations.model import Invitation
from app.shared.enums import InvitationStatus


def _con_estado(query, estado: InvitationStatus, ahora: datetime):
    """
    The status is not stored (see `InvitationStatus`): it is translated
    into the same date conditions it is computed with.
    """
    pendiente = (Invitation.accepted_at.is_(None), Invitation.revoked_at.is_(None))
    if estado is InvitationStatus.ACCEPTED:
        return query.where(Invitation.accepted_at.is_not(None))
    if estado is InvitationStatus.REVOKED:
        return query.where(Invitation.revoked_at.is_not(None))
    if estado is InvitationStatus.EXPIRED:
        return query.where(*pendiente, Invitation.expires_at <= ahora)
    return query.where(*pendiente, Invitation.expires_at > ahora)


class InvitationRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, invitation_id: UUID) -> Invitation | None:
        return self.db.get(Invitation, invitation_id)

    def get_by_code_hash(
        self, code_hash: str, for_update: bool = False
    ) -> Invitation | None:
        """
        `for_update` locks the row until the end of the transaction: it is
        what makes the link single-use even if it is accepted twice at the
        same time. The second request waits here and reads `accepted_at`
        already set. SQLite has no `FOR UPDATE` and ignores it.
        """
        query = select(Invitation).where(Invitation.code_hash == code_hash)
        if for_update:
            query = query.with_for_update().execution_options(populate_existing=True)
        return self.db.scalar(query)

    def get_pending(self, organization_id: UUID, email: str) -> Invitation | None:
        """
        The invitation of that email in that organization that is neither
        accepted nor revoked, expired or not. There can only be one
        (`uq_invitations_pending_org_email`).
        """
        return self.db.scalar(
            select(Invitation).where(
                Invitation.organization_id == organization_id,
                Invitation.email == email,
                Invitation.accepted_at.is_(None),
                Invitation.revoked_at.is_(None),
            )
        )

    def list(
        self,
        ahora: datetime,
        offset: int = 0,
        limit: int = 100,
        organization_id: UUID | None = None,
        status: InvitationStatus | None = None,
    ) -> tuple[list[Invitation], int]:
        """Newest first. No scope: only the admin lists them."""
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        query = select(Invitation)
        if organization_id is not None:
            query = query.where(Invitation.organization_id == organization_id)
        if status is not None:
            query = _con_estado(query, status, ahora)

        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = list(
            self.db.scalars(
                query.order_by(Invitation.created_at.desc(), Invitation.id)
                .offset(offset)
                .limit(limit)
            ).all()
        )
        return items, int(total or 0)

    def create(self, **campos) -> Invitation:
        invitation = Invitation(**campos)
        self.db.add(invitation)
        self.db.flush()
        return invitation
