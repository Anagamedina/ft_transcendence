"""merge contract and alert notifications heads

Revision ID: a47cf27626b1
Revises: e5a8c2f4b913, e3b8c1f5a7d9
Create Date: 2026-10-26 13:30:32.835093
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



revision: str = 'a47cf27626b1'
down_revision: Union[str, Sequence[str], None] = ('e5a8c2f4b913', 'e3b8c1f5a7d9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply this migration."""
    pass


def downgrade() -> None:
    """Revert this migration."""
    pass
