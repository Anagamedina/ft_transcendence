"""create alert_notifications (#275, provisional until #276)

Revision ID: e3b8c1f5a7d9
Revises: 9d1f4e7a3b62
Create Date: 2026-10-25

One row per notice sent to the client because nobody took the alert
(#275). PROVISIONAL: the table belongs to #276 (Daruny); it is here so the
sending can be built and tested meanwhile.

- (alert_id, attempt) is unique: the notice is written before it is sent,
  so a restart can never send the same one twice.
- ON DELETE CASCADE: deleting an alert deletes its notices.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e3b8c1f5a7d9"
down_revision: Union[str, Sequence[str], None] = "9d1f4e7a3b62"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "alert_notifications",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "alert_id",
            sa.Uuid(),
            sa.ForeignKey(
                "alerts.id",
                name="fk_alert_notifications_alert_id_alerts",
                ondelete="CASCADE",
            ),
            nullable=False,
        ),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("channel", sa.String(20), nullable=False, server_default="EMAIL"),
        sa.Column("recipient", sa.Text(), nullable=False),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("alert_id", "attempt", name="uq_alert_notifications_alert_attempt"),
        sa.CheckConstraint("channel IN ('EMAIL')", name="ck_alert_notifications_channel"),
        sa.CheckConstraint("attempt >= 1", name="ck_alert_notifications_attempt"),
    )
    op.create_index("ix_alert_notifications_alert_id", "alert_notifications", ["alert_id"])


def downgrade() -> None:
    op.drop_index("ix_alert_notifications_alert_id", table_name="alert_notifications")
    op.drop_table("alert_notifications")
