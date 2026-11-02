"""add organization contract: period, sites, sensors, price (B14)

Revision ID: e5a8c2f4b913
Revises: 9d1f4e7a3b62
Create Date: 2026-10-25

"Hazte cliente" stores what the client contracts and what it pays:

- billing_period: MONTHLY or YEARLY (BillingPeriod). NULL until the client subscribes.
- contracted_sites, contracted_sensors: what the client pays for. They are
  also its limits: an admin cannot add more buildings or sensors.
- monthly_price_eur: the monthly price agreed when subscribing (plan base
  plus each sensor), kept even if the prices change later.
- postal_code: fiscal postal code, apart from billing_address.
- sepa_accepted_at: when the client authorized the SEPA direct debit.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e5a8c2f4b913"
down_revision: Union[str, Sequence[str], None] = "9d1f4e7a3b62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "organizations", sa.Column("billing_period", sa.String(10), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("contracted_sites", sa.Integer(), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("contracted_sensors", sa.Integer(), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("monthly_price_eur", sa.Integer(), nullable=True)
    )
    op.add_column(
        "organizations", sa.Column("postal_code", sa.String(10), nullable=True)
    )
    op.add_column(
        "organizations",
        sa.Column("sepa_accepted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_check_constraint(
        "ck_organizations_billing_period",
        "organizations",
        "billing_period IS NULL OR billing_period IN ('MONTHLY', 'YEARLY')",
    )
    op.create_check_constraint(
        "ck_organizations_contract",
        "organizations",
        "(contracted_sites IS NULL OR contracted_sites >= 1) "
        "AND (contracted_sensors IS NULL OR contracted_sensors >= 1) "
        "AND (monthly_price_eur IS NULL OR monthly_price_eur >= 0)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_organizations_contract", "organizations", type_="check")
    op.drop_constraint(
        "ck_organizations_billing_period", "organizations", type_="check"
    )
    op.drop_column("organizations", "sepa_accepted_at")
    op.drop_column("organizations", "postal_code")
    op.drop_column("organizations", "monthly_price_eur")
    op.drop_column("organizations", "contracted_sensors")
    op.drop_column("organizations", "contracted_sites")
    op.drop_column("organizations", "billing_period")
