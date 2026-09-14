"""Persistence queries for users."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.modules.users.model import User


def normalize_email(email: str) -> str:
    return email.strip().lower()


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(
            select(User).where(User.email == normalize_email(email))
        )

    def get_by_id(self, user_id: UUID, organization_id: UUID) -> User | None:
        return self.db.scalar(
            select(User).where(
                User.id == user_id,
                User.organization_id == organization_id,
            )
        )

    def create(
        self,
        organization_id: UUID,
        email: str,
        password_hash: str,
        role: str,
    ) -> User:
        user = User(
            organization_id=organization_id,
            email=normalize_email(email),
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
