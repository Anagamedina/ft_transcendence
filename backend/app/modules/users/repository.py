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
        Busca un usuario solo por su id, SIN filtrar por organización.

        Es la excepción de este módulo y conviene saber por qué existe. La
        usa la resolución de sesión (`get_current_user`, issue #26): la
        cookie solo lleva el id, y la organización del usuario es
        precisamente el dato que se quiere averiguar — no se puede exigir
        como filtro lo que todavía no se sabe.

        No sustituye a `get_by_id`: para lo que pida un usuario con sesión
        sobre OTRO usuario se sigue usando aquel, que sí aísla por
        organización.
        """
        return self.db.scalar(select(User).where(User.id == user_id))

    # Añadidos para la gestión de usuarios de la B6 (#141). Sin alcance por
    # organización: solo los usa el admin, y eso lo comprueba el router.
    def list(
        self,
        offset: int = 0,
        limit: int = 100,
        organization_id: UUID | None = None,
        q: str | None = None,
        active: bool | None = None,
    ) -> tuple[list[User], int]:
        """Usuarios por nombre. `q` busca en el nombre y el email."""
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
                # El id desempata para que la paginación no repita ni salte.
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
