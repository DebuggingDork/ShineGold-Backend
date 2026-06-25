"""add photo GPS, user home coords, MCQ unique constraint

Revision ID: a3f8c2d91e47
Revises: 514b4fe05bb3
Create Date: 2026-06-25 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a3f8c2d91e47"
down_revision: Union[str, Sequence[str], None] = "514b4fe05bb3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("home_lat", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("home_lng", sa.Float(), nullable=True))

    op.add_column("visit_photos", sa.Column("captured_lat", sa.Float(), nullable=False))
    op.add_column("visit_photos", sa.Column("captured_lng", sa.Float(), nullable=False))
    op.add_column("visit_photos", sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False))

    op.create_unique_constraint(
        "uq_visit_mcq_answers_visit_question",
        "visit_mcq_answers",
        ["visit_id", "question_key"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_visit_mcq_answers_visit_question", "visit_mcq_answers", type_="unique")

    op.drop_column("visit_photos", "captured_at")
    op.drop_column("visit_photos", "captured_lng")
    op.drop_column("visit_photos", "captured_lat")

    op.drop_column("users", "home_lng")
    op.drop_column("users", "home_lat")
