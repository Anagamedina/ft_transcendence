# MODEL — organizations
# SQLAlchemy model for organizations table
from datetime import datetime

from sqlalchemy import DateTime, BigInteger, Identify, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(
        BigInteger,
        Identify(),
        primary_key=True
    )
    name: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    create_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    update_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
