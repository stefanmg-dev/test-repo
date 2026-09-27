"""add invoice shadow validation metadata

Revision ID: e4a1b2c3d4f5
Revises: 6fc8c5caeaba
Create Date: 2026-09-27 21:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4a1b2c3d4f5"
down_revision: Union[str, Sequence[str], None] = "6fc8c5caeaba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processing_runs",
        sa.Column(
            "invoice_schema_version",
            sa.String(length=20),
            nullable=True,
        ),
    )
    op.add_column(
        "processing_runs",
        sa.Column(
            "invoice_shadow_validation_status",
            sa.String(length=20),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "processing_runs",
        "invoice_shadow_validation_status",
    )
    op.drop_column(
        "processing_runs",
        "invoice_schema_version",
    )
