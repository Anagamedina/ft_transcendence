"""Persistence queries for users."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.users.model import User
from app.shared.fields import normalize_email
from app.shared.utils import matches_text




class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(
            select(User).where(User.email == normalize_email(email))
        )

    def get_by_id(self, user_id: UUID, organization_id: UUID | None) -> User | None:
        return self.db.scalar(
            select(User).where(
                User.id == user_id,
                User.organization_id == organization_id,
            )
        )

    def get(self, user_id: UUID) -> User | None:
        """
        Looks a user up by id alone, WITHOUT filtering by organization.

        It is the exception of this module and worth knowing why it exists.
        The session resolution uses it (`get_current_user`, issue #26): the
        cookie only holds the id, and the user's organization is exactly
        what we want to find out — what is not known yet cannot be
        required as a filter.

        It does not replace `get_by_id`: whatever a user with a session
        asks about ANOTHER user still uses that one, which does isolate by
        organization.
        """
        return self.db.scalar(select(User).where(User.id == user_id))

    # Added for the B6 user management (#141). No organization scope: only
    # the admin uses them, and the router checks that.
    def list(
        self,
        offset: int = 0,
        limit: int = 100,
        organization_id: UUID | None = None,
        q: str | None = None,
        active: bool | None = None,
    ) -> tuple[list[User], int]:
        """Users by name. `q` searches the name and the email."""
        if offset < 0 or limit <= 0:
            raise ValueError("Invalid pagination")

        query = select(User)
        if organization_id is not None:
            query = query.where(User.organization_id == organization_id)
        if q is not None:
            query = query.where(matches_text(q, User.name, User.email))
        if active is not None:
            query = query.where(User.is_active == active)

        total = self.db.scalar(select(func.count()).select_from(query.subquery()))
        items = list(
            self.db.scalars(
                # The id breaks ties so pagination never repeats or skips.
                query.order_by(User.name, User.id).offset(offset).limit(limit)
            ).all()
        )
        return items, int(total or 0)

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.flush()

    def create(
        self,
        organization_id: UUID | None,
        email: str,
        name: str,
        password_hash: str,
        role: str,
    ) -> User:
        user = User(
            organization_id=organization_id,
            email=normalize_email(email),
            name=name,
            password_hash=password_hash,
            role=role,
        )
        self.db.add(user)
        try:
            self.db.flush()
        except SQLAlchemyError:
            self.db.rollback()
            raise

        return user
