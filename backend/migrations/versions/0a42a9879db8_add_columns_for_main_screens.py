"""add columns for main screens: org status and contact, site floors, sensor floor, user activity, alert actors

Revision ID: 0a42a9879db8
Revises: 5fd57f2fb8ae
Create Date: 2026-10-08
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0a42a9879db8"
down_revision: Union[str, Sequence[str], None] = "5fd57f2fb8ae"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # organizations: existing rows get status ACTIVE through the server default,
    # so the CHECK below already holds when it is created.
    op.add_column(
        "organizations",
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="ACTIVE",
        ),
    )
    op.create_check_constraint(
        "ck_organizations_status",
        "organizations",
        "status IN ('TRIAL', 'ACTIVE', 'SUSPENDED')",
    )
    op.add_column(
        "organizations",
        sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("organizations", sa.Column("city", sa.String(length=120), nullable=True))
    op.add_column(
        "organizations", sa.Column("contact_email", sa.String(length=320), nullable=True)
    )
    op.add_column("organizations", sa.Column("phone", sa.String(length=30), nullable=True))
    op.add_column(
        "organizations", sa.Column("legal_name", sa.String(length=200), nullable=True)
    )
    op.add_column("organizations", sa.Column("tax_id", sa.String(length=30), nullable=True))
    op.add_column(
        "organizations", sa.Column("billing_email", sa.String(length=320), nullable=True)
    )

    # sites: existing buildings become 1 floor, no basements, type OTHER.
    op.add_column(
        "sites",
        sa.Column("floors", sa.Integer(), nullable=False, server_default="1"),
    )
    op.add_column(
        "sites",
        sa.Column("basements", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "sites",
        sa.Column(
            "building_type",
            sa.String(length=20),
            nullable=False,
            server_default="OTHER",
        ),
    )
    op.create_check_constraint(
        "ck_sites_building_type",
        "sites",
        "building_type IN ('HOTEL', 'COMMUNITY', 'OFFICE', 'SPORTS', "
        "'RESIDENCE', 'INDUSTRIAL', 'OTHER')",
    )
    op.create_check_constraint(
        "ck_sites_floors",
        "sites",
        "floors >= 1 AND basements >= 0",
    )

    # sensors: existing sensors are on the ground floor.
    op.add_column(
        "sensors",
        sa.Column("floor", sa.Integer(), nullable=False, server_default="0"),
    )

    # users: existing users stay active; the rest are unknown, so NULL.
    op.add_column(
        "users",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.add_column(
        "users",
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("terms_version", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("terms_accepted_at", sa.DateTime(timezone=True), nullable=True),
    )

    # alerts: nobody is recorded for past acknowledgements and resolutions.
    op.add_column(
        "alerts",
        sa.Column("acknowledged_by", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.add_column(
        "alerts",
        sa.Column("resolved_by", sa.Uuid(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_alerts_acknowledged_by_users",
        "alerts",
        "users",
        ["acknowledged_by"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_foreign_key(
        "fk_alerts_resolved_by_users",
        "alerts",
        "users",
        ["resolved_by"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    # Drops data: the values stored in these columns are lost.
    op.drop_constraint("fk_alerts_resolved_by_users", "alerts", type_="foreignkey")
    op.drop_constraint("fk_alerts_acknowledged_by_users", "alerts", type_="foreignkey")
    op.drop_column("alerts", "resolved_by")
    op.drop_column("alerts", "acknowledged_by")

    op.drop_column("users", "terms_accepted_at")
    op.drop_column("users", "terms_version")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "is_active")

    op.drop_column("sensors", "floor")

    op.drop_constraint("ck_sites_floors", "sites", type_="check")
    op.drop_constraint("ck_sites_building_type", "sites", type_="check")
    op.drop_column("sites", "building_type")
    op.drop_column("sites", "basements")
    op.drop_column("sites", "floors")

    op.drop_column("organizations", "billing_email")
    op.drop_column("organizations", "tax_id")
    op.drop_column("organizations", "legal_name")
    op.drop_column("organizations", "phone")
    op.drop_column("organizations", "contact_email")
    op.drop_column("organizations", "city")
    op.drop_column("organizations", "trial_ends_at")
    op.drop_constraint("ck_organizations_status", "organizations", type_="check")
    op.drop_column("organizations", "status")
