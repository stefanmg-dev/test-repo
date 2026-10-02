"""add processing run extraction evidence

Revision ID: a6c3d4e5f7b8
Revises: f5b2c3d4e6a7
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "a6c3d4e5f7b8"
down_revision: str | None = "f5b2c3d4e6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "processing_runs",
        sa.Column(
            "field_evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )
    op.add_column(
        "processing_runs",
        sa.Column(
            "collection_evidence",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("processing_runs", "collection_evidence")
    op.drop_column("processing_runs", "field_evidence")
