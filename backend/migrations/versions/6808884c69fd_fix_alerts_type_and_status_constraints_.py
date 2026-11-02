"""fix alerts type and status constraints, add message

Revision ID: 6808884c69fd
Revises: b506173c2aac
Create Date: 2026-09-18 23:12:38.725604
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = '6808884c69fd'
down_revision: Union[str, Sequence[str], None] = 'b506173c2aac'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply this migration."""
    op.drop_constraint("ck_alerts_type", "alerts", type_="check")
    op.create_check_constraint(
        "ck_alerts_type",
        "alerts",
        "alert_type IN ('LOW_PRESSURE', 'HIGH_PRESSURE', 'SENSOR_OFFLINE')",
    )

    op.drop_constraint("ck_alerts_status", "alerts", type_="check")
    op.create_check_constraint(
        "ck_alerts_status",
        "alerts",
        "status IN ('ACTIVE', 'RESOLVED')",
    )

    op.drop_constraint("ck_alerts_severity", "alerts", type_="check")
    op.create_check_constraint(
        "ck_alerts_severity",
        "alerts",
        "severity IN ('WARNING', 'CRITICAL')",
    )


def downgrade() -> None:
    """Revert this migration."""
    op.drop_constraint("ck_alerts_severity", "alerts", type_="check")
    op.create_check_constraint(
        "ck_alerts_severity",
        "alerts",
        "severity IN ('INFO', 'WARNING', 'CRITICAL')",
    )

    op.drop_constraint("ck_alerts_status", "alerts", type_="check")
    op.create_check_constraint(
        "ck_alerts_status",
        "alerts",
        "status IN ('OPEN', 'ACKNOWLEDGED', 'RESOLVED')",
    )

    op.drop_constraint("ck_alerts_type", "alerts", type_="check")
    op.create_check_constraint(
        "ck_alerts_type",
        "alerts",
        "alert_type IN ('LOW', 'HIGH', 'OFFLINE')",
    )
