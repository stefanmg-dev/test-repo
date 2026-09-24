"""Add identity persistence

Revision ID: c7f1a2b3d4e5
Revises: b88bfcb21ad6
Create Date: 2026-09-24 20:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c7f1a2b3d4e5"
down_revision: Union[str, Sequence[str], None] = "b88bfcb21ad6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processing_runs",
        sa.Column(
            "tenant_id",
            sa.String(length=100),
            server_default="default",
            nullable=False,
        ),
    )
    op.add_column(
        "processing_runs",
        sa.Column(
            "created_by_type",
            sa.String(length=20),
            server_default="system",
            nullable=False,
        ),
    )
    op.add_column(
        "processing_runs",
        sa.Column(
            "created_by_subject",
            sa.String(length=255),
            server_default="legacy",
            nullable=False,
        ),
    )
    op.create_index(
        "ix_processing_runs_tenant_id",
        "processing_runs",
        ["tenant_id"],
        unique=False,
    )
    op.create_table(
        "api_keys",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("tenant_id", sa.String(length=100), nullable=False),
        sa.Column("secret_hash", sa.String(length=64), nullable=False),
        sa.Column("secret_prefix", sa.String(length=32), nullable=False),
        sa.Column(
            "scopes",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "expires_at IS NULL OR expires_at > created_at",
            name="ck_api_keys_expiry_after_creation",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_api_keys_secret_prefix",
        "api_keys",
        ["secret_prefix"],
        unique=True,
    )
    op.create_index(
        "ix_api_keys_tenant_id",
        "api_keys",
        ["tenant_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_api_keys_tenant_id", table_name="api_keys")
    op.drop_index("ix_api_keys_secret_prefix", table_name="api_keys")
    op.drop_table("api_keys")
    op.drop_index(
        "ix_processing_runs_tenant_id",
        table_name="processing_runs",
    )
    op.drop_column("processing_runs", "created_by_subject")
    op.drop_column("processing_runs", "created_by_type")
    op.drop_column("processing_runs", "tenant_id")
