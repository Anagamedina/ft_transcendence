"""create documents table

Revision ID: 81bfe9714e30
Revises: edcf330361ab
Create Date: 2026-10-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "81bfe9714e30"
down_revision: Union[str, Sequence[str], None] = "edcf330361ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # New table: no existing rows, so no defaults or backfill are needed.
    op.create_table(
        "documents",
        sa.Column(
            "id",
            sa.Uuid(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("organization_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("site_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=255), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("uploaded_by", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "kind IN ('PLAN', 'REPORT', 'INVOICE', 'PHOTO', 'OTHER')",
            name="ck_documents_kind",
        ),
        sa.CheckConstraint("size >= 0", name="ck_documents_size"),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
            name="fk_documents_organization_id_organizations",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["site_id"],
            ["sites.id"],
            name="fk_documents_site_id_sites",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by"],
            ["users.id"],
            name="fk_documents_uploaded_by_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("storage_key", name="uq_documents_storage_key"),
    )
    op.create_index(
        "ix_documents_site_created_at",
        "documents",
        ["site_id", "created_at"],
    )


def downgrade() -> None:
    # Drops data: the metadata of every document is lost (the files in the
    # storage are not touched).
    op.drop_index("ix_documents_site_created_at", table_name="documents")
    op.drop_table("documents")
