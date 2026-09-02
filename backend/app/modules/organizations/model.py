# MODEL - organizations
# SQLAlchemy model for organizations table
from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, BigInteger, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identity(),
        primary_key=True
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ORM relationship with the parent site
    users: Mapped[list["User"]] = relationship(
        "User",
        back_populates="organization",
    )

    # Organization.sites <-> Site.organization
    sites: Mapped[list["Site"]] = relationship(
        "Site",
        back_populates="organization",
    )
