"""farm multi-executive assignments

Revision ID: b7e4a1c92f03
Revises: a3f8c2d91e47
Create Date: 2026-07-09 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "b7e4a1c92f03"
down_revision: Union[str, Sequence[str], None] = "a3f8c2d91e47"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "farm_executive_assignments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("executive_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("assigned_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["executive_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("farm_id", "executive_id", name="uq_farm_executive_assignment"),
    )

    op.execute(
        """
        INSERT INTO farm_executive_assignments (id, farm_id, executive_id, assigned_by, assigned_at)
        SELECT gen_random_uuid(), id, assigned_executive_id, onboarded_by, created_at
        FROM farms
        WHERE assigned_executive_id IS NOT NULL
        """
    )

    op.drop_constraint("farms_assigned_executive_id_fkey", "farms", type_="foreignkey")
    op.drop_column("farms", "assigned_executive_id")
    op.alter_column("farms", "onboarded_by", existing_type=postgresql.UUID(), nullable=True)


def downgrade() -> None:
    op.add_column(
        "farms",
        sa.Column("assigned_executive_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "farms_assigned_executive_id_fkey",
        "farms",
        "users",
        ["assigned_executive_id"],
        ["id"],
    )

    op.execute(
        """
        UPDATE farms AS f
        SET assigned_executive_id = sub.executive_id
        FROM (
            SELECT DISTINCT ON (farm_id) farm_id, executive_id
            FROM farm_executive_assignments
            ORDER BY farm_id, assigned_at ASC
        ) AS sub
        WHERE f.id = sub.farm_id
        """
    )

    op.alter_column("farms", "onboarded_by", existing_type=postgresql.UUID(), nullable=False)
    op.drop_table("farm_executive_assignments")
