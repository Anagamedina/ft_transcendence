"""users: a client always belongs to an organization

Revision ID: 8e879672702c
Revises: 0a42a9879db8
Create Date: 2026-10-08
"""

from typing import Sequence, Union

from alembic import op


revision: str = "8e879672702c"
down_revision: Union[str, Sequence[str], None] = "0a42a9879db8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Clients without an organization are not fixed here: there is no right
    # organization to assign them. If one exists, this fails on purpose. Find
    # them with: SELECT id, email FROM users
    #            WHERE role <> 'admin' AND organization_id IS NULL;
    op.create_check_constraint(
        "ck_users_client_has_organization",
        "users",
        "role = 'admin' OR organization_id IS NOT NULL",
    )


def downgrade() -> None:
    op.drop_constraint("ck_users_client_has_organization", "users", type_="check")
