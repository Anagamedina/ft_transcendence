"""organizations name length 120 and unique lower name

Revision ID: 5fd57f2fb8ae
Revises: d7f2a9c4e1b8
Create Date: 2026-10-04 12:36:32.973464
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "5fd57f2fb8ae"
down_revision: Union[str, Sequence[str], None] = "d7f2a9c4e1b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Same max length as OrganizationCreate.name in schemas.py.
    op.alter_column(
        "organizations",
        "name",
        existing_type=sa.VARCHAR(length=50),
        type_=sa.String(length=120),
        existing_nullable=False,
    )
    # Duplicates are not merged: if two names only differ in case, this fails on purpose.
    op.create_index(
        "uq_organizations_name_lower",
        "organizations",
        [sa.literal_column("lower(name)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_organizations_name_lower", table_name="organizations")
    # Names are not truncated: if one is longer than 50, this fails on purpose.
    op.alter_column(
        "organizations",
        "name",
        existing_type=sa.String(length=120),
        type_=sa.VARCHAR(length=50),
        existing_nullable=False,
    )
