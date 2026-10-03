"""align sensors with contract: location, sensor_type, required thresholds, unit default

Revision ID: d7f2a9c4e1b8
Revises: c4e0b1a3d2f7
Create Date: 2026-10-03
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d7f2a9c4e1b8"
down_revision: Union[str, Sequence[str], None] = "c4e0b1a3d2f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sensors",
        sa.Column("location", sa.String(length=120), nullable=True),
    )
    op.add_column(
        "sensors",
        sa.Column(
            "sensor_type",
            sa.String(length=20),
            nullable=False,
            server_default="PRESSURE",
        ),
    )
    op.create_check_constraint(
        "ck_sensors_type",
        "sensors",
        "sensor_type IN ('PRESSURE', 'FLOW')",
    )

    # Thresholds are not backfilled: if a row still has NULLs, this fails on purpose.
    op.drop_constraint("ck_sensors_threshold_order", "sensors", type_="check")
    op.alter_column(
        "sensors",
        "low_threshold",
        existing_type=sa.Numeric(precision=10, scale=3),
        nullable=False,
    )
    op.alter_column(
        "sensors",
        "high_threshold",
        existing_type=sa.Numeric(precision=10, scale=3),
        nullable=False,
    )
    op.create_check_constraint(
        "ck_sensors_threshold_order",
        "sensors",
        "low_threshold < high_threshold",
    )
    # Same bar range as PRESSURE_MIN_BAR / PRESSURE_MAX_BAR in schemas.py.
    op.create_check_constraint(
        "ck_sensors_threshold_range",
        "sensors",
        "low_threshold >= 0 AND high_threshold <= 25",
    )

    op.alter_column(
        "sensors",
        "unit",
        existing_type=sa.String(length=20),
        server_default="bar",
    )


def downgrade() -> None:
    op.alter_column(
        "sensors",
        "unit",
        existing_type=sa.String(length=20),
        server_default=None,
    )

    op.drop_constraint("ck_sensors_threshold_range", "sensors", type_="check")
    op.drop_constraint("ck_sensors_threshold_order", "sensors", type_="check")
    op.alter_column(
        "sensors",
        "high_threshold",
        existing_type=sa.Numeric(precision=10, scale=3),
        nullable=True,
    )
    op.alter_column(
        "sensors",
        "low_threshold",
        existing_type=sa.Numeric(precision=10, scale=3),
        nullable=True,
    )
    op.create_check_constraint(
        "ck_sensors_threshold_order",
        "sensors",
        "low_threshold IS NULL "
        "OR high_threshold IS NULL "
        "OR low_threshold < high_threshold",
    )

    op.drop_constraint("ck_sensors_type", "sensors", type_="check")
    op.drop_column("sensors", "sensor_type")
    op.drop_column("sensors", "location")