"""add user name and optional organization

Revision ID: c4e0b1a3d2f7
Revises: a13f38c31f88
Create Date: 2026-09-26
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e0b1a3d2f7"
down_revision: Union[str, Sequence[str], None] = "a13f38c31f88"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "name",
            sa.String(length=120),
            nullable=False,
            server_default="Migrated User",
        ),
    )
    op.alter_column(
        "users",
        "name",
        existing_type=sa.String(length=120),
        server_default=None,
    )
    op.alter_column(
        "users",
        "organization_id",
        existing_type=sa.Uuid(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "users",
        "organization_id",
        existing_type=sa.Uuid(as_uuid=True),
        nullable=False,
    )
    op.drop_column("users", "name")
