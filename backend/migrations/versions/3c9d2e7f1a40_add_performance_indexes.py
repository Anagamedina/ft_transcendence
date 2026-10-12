"""add performance indexes (D5)

Revision ID: 3c9d2e7f1a40
Revises: 29b0a4e9f2ae
Create Date: 2026-10-11

Indexes for the queries of the design, checked with EXPLAIN ANALYZE on a
bench database (1.6M readings, 200k alerts, 4k users):

- readings(sensor_id, created_at): last reading per sensor (sensor status
  and the offline rule).
- alerts(status, severity, created_at): alert list filtered by severity.
  alerts(status, created_at) stays: without it a list filtered only by
  status sorts every row.
- alerts(sensor_id, status): the open alert of a sensor, on every reading.
- users(organization_id): users of an organization.

sites(organization_id) is already covered by uq_sites_organization_name,
which starts with that column.
"""

from typing import Sequence, Union

from alembic import op


revision: str = "3c9d2e7f1a40"
down_revision: Union[str, Sequence[str], None] = "29b0a4e9f2ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_readings_sensor_created_at", "readings", ["sensor_id", "created_at"]
    )
    op.create_index(
        "ix_alerts_status_severity_created_at",
        "alerts",
        ["status", "severity", "created_at"],
    )
    op.create_index("ix_alerts_sensor_status", "alerts", ["sensor_id", "status"])
    op.create_index("ix_users_organization_id", "users", ["organization_id"])


def downgrade() -> None:
    op.drop_index("ix_users_organization_id", table_name="users")
    op.drop_index("ix_alerts_sensor_status", table_name="alerts")
    op.drop_index("ix_alerts_status_severity_created_at", table_name="alerts")
    op.drop_index("ix_readings_sensor_created_at", table_name="readings")
