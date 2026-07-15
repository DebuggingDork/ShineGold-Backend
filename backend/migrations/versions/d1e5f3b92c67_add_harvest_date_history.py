"""Add harvest_date_history audit table.

Revision ID: d1e5f3b92c67
Revises: c9d4e2a81b56
Create Date: 2026-07-15 11:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "d1e5f3b92c67"
down_revision: Union[str, Sequence[str], None] = "c9d4e2a81b56"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "harvest_date_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("old_date", sa.Date(), nullable=False),
        sa.Column("new_date", sa.Date(), nullable=False),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "changed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_harvest_date_history_farm_id",
        "harvest_date_history",
        ["farm_id"],
        unique=False,
    )
    op.create_index(
        "ix_harvest_date_history_changed_by",
        "harvest_date_history",
        ["changed_by"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_harvest_date_history_changed_by", table_name="harvest_date_history")
    op.drop_index("ix_harvest_date_history_farm_id", table_name="harvest_date_history")
    op.drop_table("harvest_date_history")
