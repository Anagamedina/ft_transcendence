"""add site district

Revision ID: 29b0a4e9f2ae
Revises: 81bfe9714e30
Create Date: 2026-10-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "29b0a4e9f2ae"
down_revision: Union[str, Sequence[str], None] = "81bfe9714e30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable and without default: the existing sites have no known district,
    # so they stay NULL instead of getting an invented one (ADR 0004, rule 1).
    op.add_column(
        "sites", sa.Column("district", sa.String(length=30), nullable=True)
    )
    # Every current row is NULL, so the CHECK cannot fail on existing data.
    op.create_check_constraint(
        "ck_sites_district",
        "sites",
        "district IS NULL OR district IN ('CIUTAT_VELLA', 'EIXAMPLE', "
        "'SANTS_MONTJUIC', 'LES_CORTS', 'SARRIA_SANT_GERVASI', 'GRACIA', "
        "'HORTA_GUINARDO', 'NOU_BARRIS', 'SANT_ANDREU', 'SANT_MARTI')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_sites_district", "sites", type_="check")
    op.drop_column("sites", "district")
