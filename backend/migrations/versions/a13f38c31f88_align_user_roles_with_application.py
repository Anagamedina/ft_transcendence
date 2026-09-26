"""align user roles with application

Revision ID: a13f38c31f88
Revises: 6808884c69fd
Create Date: 2026-09-26 20:44:25.724399
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = 'a13f38c31f88'
down_revision: Union[str, Sequence[str], None] = '6808884c69fd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("ck_users_role", "users", type_="check")

    op.execute("UPDATE users SET role = LOWER(role)")

    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('admin', 'client')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_role", "users", type_="check")

    op.execute("UPDATE users SET role = UPPER(role)")

    op.create_check_constraint(
        "ck_users_role",
        "users",
        "role IN ('ADMIN', 'CLIENT')",
    )
