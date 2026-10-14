"""add organization subscription (B14)

Revision ID: 4b7e1c9a2d53
Revises: 3c9d2e7f1a40
Create Date: 2026-10-14

A TRIAL client can subscribe from the app (B14, issue #150):

- plan: BASIC, PRO or ENTERPRISE (SubscriptionPlan). NULL until then.
- subscribed_at: when the client subscribed.
- billing_address: fiscal address, next to legal_name and tax_id (D1).
- iban_masked: only the masked IBAN. The real one is never stored.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "4b7e1c9a2d53"
down_revision: Union[str, Sequence[str], None] = "3c9d2e7f1a40"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organizations", sa.Column("billing_address", sa.String(200), nullable=True)
    )
    op.add_column("organizations", sa.Column("plan", sa.String(20), nullable=True))
    op.add_column(
        "organizations",
        sa.Column("subscribed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "organizations", sa.Column("iban_masked", sa.String(42), nullable=True)
    )
    op.create_check_constraint(
        "ck_organizations_plan",
        "organizations",
        "plan IS NULL OR plan IN ('BASIC', 'PRO', 'ENTERPRISE')",
    )


def downgrade() -> None:
    op.drop_constraint("ck_organizations_plan", "organizations", type_="check")
    op.drop_column("organizations", "iban_masked")
    op.drop_column("organizations", "subscribed_at")
    op.drop_column("organizations", "plan")
    op.drop_column("organizations", "billing_address")
