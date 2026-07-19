"""add farmer aadhar_number and farm plant_count

Revision ID: e2f6a4c03d78
Revises: d1e5f3b92c67
Create Date: 2026-07-18 16:20:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e2f6a4c03d78"
down_revision: Union[str, None] = "d1e5f3b92c67"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "farmers",
        sa.Column("aadhar_number", sa.String(length=12), nullable=True),
    )
    op.add_column(
        "farms",
        sa.Column("plant_count", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("farms", "plant_count")
    op.drop_column("farmers", "aadhar_number")
