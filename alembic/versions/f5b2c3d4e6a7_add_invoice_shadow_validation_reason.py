"""add invoice shadow validation reason

Revision ID: f5b2c3d4e6a7
Revises: e4a1b2c3d4f5
Create Date: 2026-09-28 19:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f5b2c3d4e6a7"
down_revision: Union[str, Sequence[str], None] = "e4a1b2c3d4f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "processing_runs",
        sa.Column(
            "invoice_shadow_validation_reason",
            sa.String(length=40),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "processing_runs",
        "invoice_shadow_validation_reason",
    )
