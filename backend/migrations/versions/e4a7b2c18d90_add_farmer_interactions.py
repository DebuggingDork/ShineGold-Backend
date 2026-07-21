"""Add farmer_interactions prospect log table.

Revision ID: e4a7b2c18d90
Revises: e2f6a4c03d78
Create Date: 2026-07-21 11:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "e4a7b2c18d90"
down_revision: Union[str, Sequence[str], None] = "e2f6a4c03d78"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    interaction_status = postgresql.ENUM(
        "READY_TO_ONBOARD",
        "TAKING_TIME",
        "UNCERTAIN",
        name="interaction_status",
        create_type=True,
    )
    interaction_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "farmer_interactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("executive_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("farmer_name", sa.String(length=255), nullable=False),
        sa.Column("phone_number", sa.String(length=20), nullable=False),
        sa.Column("land_location", sa.String(length=500), nullable=False),
        sa.Column("acres", sa.Float(), nullable=False),
        sa.Column("current_crop", sa.String(length=255), nullable=False),
        sa.Column("planned_months", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            postgresql.ENUM(
                "READY_TO_ONBOARD",
                "TAKING_TIME",
                "UNCERTAIN",
                name="interaction_status",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["executive_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_farmer_interactions_executive_id",
        "farmer_interactions",
        ["executive_id"],
        unique=False,
    )
    op.create_index(
        "ix_farmer_interactions_status",
        "farmer_interactions",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_farmer_interactions_status", table_name="farmer_interactions")
    op.drop_index("ix_farmer_interactions_executive_id", table_name="farmer_interactions")
    op.drop_table("farmer_interactions")
    op.execute("DROP TYPE IF EXISTS interaction_status")
