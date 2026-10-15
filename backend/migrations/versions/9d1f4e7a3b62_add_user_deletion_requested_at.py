"""add users.deletion_requested_at (B15)

Revision ID: 9d1f4e7a3b62
Revises: 4b7e1c9a2d53
Create Date: 2026-10-15

A user can ask to close their account from "Mi cuenta" (B15, issue #149):

- deletion_requested_at: when they asked. NULL if they never did, so
  existing users need no default. An admin acts on it by hand; nothing is
  deleted automatically.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "9d1f4e7a3b62"
down_revision: Union[str, Sequence[str], None] = "4b7e1c9a2d53"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("deletion_requested_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "deletion_requested_at")
