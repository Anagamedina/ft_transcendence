"""sites and sensors name length 120

Revision ID: 55acdfbb7da1
Revises: 8e879672702c
Create Date: 2026-10-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "55acdfbb7da1"
down_revision: Union[str, Sequence[str], None] = "8e879672702c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Same max length as SiteBase.name and SensorBase.name in schemas.py: the
    # API never accepted more than 120. Names are not truncated: if one is
    # longer, this fails on purpose. Find them with:
    #   SELECT id, name FROM sites WHERE length(name) > 120;
    #   SELECT id, name FROM sensors WHERE length(name) > 120;
    op.alter_column(
        "sites",
        "name",
        existing_type=sa.VARCHAR(length=150),
        type_=sa.String(length=120),
        existing_nullable=False,
    )
    op.alter_column(
        "sensors",
        "name",
        existing_type=sa.VARCHAR(length=150),
        type_=sa.String(length=120),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "sensors",
        "name",
        existing_type=sa.String(length=120),
        type_=sa.VARCHAR(length=150),
        existing_nullable=False,
    )
    op.alter_column(
        "sites",
        "name",
        existing_type=sa.String(length=120),
        type_=sa.VARCHAR(length=150),
        existing_nullable=False,
    )
