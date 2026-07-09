"""Visit form template tables + default Jackfruit field report seed.

Revision ID: c9d4e2a81b56
Revises: b7e4a1c92f03
Create Date: 2026-07-09 13:00:00.000000

"""
import json
import uuid
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c9d4e2a81b56"
down_revision: Union[str, Sequence[str], None] = "b7e4a1c92f03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TEMPLATE_ID = "a1000000-0000-4000-8000-000000000001"


def _matrix_config() -> str:
    return json.dumps(
        {
            "rows": [
                {"key": "irrigation_system", "label": "Irrigation System Functionality"},
                {"key": "field_fencing", "label": "Field Fencing/Boundary Integrity"},
                {"key": "weed_management", "label": "Weed Management"},
                {"key": "fertigation_system", "label": "Fertigation System"},
            ],
            "columns": [
                {"key": "poor", "label": "Poor"},
                {"key": "fair", "label": "Fair"},
                {"key": "good", "label": "Good"},
                {"key": "excellent", "label": "Excellent"},
            ],
        }
    )


def _rating_config() -> str:
    return json.dumps(
        {
            "min": 1,
            "max": 5,
            "min_label": "Low Adoption",
            "max_label": "High Adoption",
        }
    )


def upgrade() -> None:
    form_question_type = postgresql.ENUM(
        "single_choice",
        "multi_choice",
        "rating_scale",
        "matrix",
        "text",
        "textarea",
        "section_header",
        name="form_question_type",
        create_type=False,
    )
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE form_question_type AS ENUM (
                'single_choice', 'multi_choice', 'rating_scale', 'matrix',
                'text', 'textarea', 'section_header'
            );
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    op.create_table(
        "visit_form_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
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
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "visit_form_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_key", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=500), nullable=False),
        sa.Column("help_text", sa.Text(), nullable=True),
        sa.Column("question_type", form_question_type, nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("config", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["template_id"], ["visit_form_templates.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("template_id", "question_key", name="uq_visit_form_question_key"),
    )

    op.create_table(
        "visit_form_question_options",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("value", sa.String(length=100), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["question_id"], ["visit_form_questions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "visit_form_answers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("visit_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_key", sa.String(length=100), nullable=False),
        sa.Column("question_label", sa.String(length=500), nullable=False),
        sa.Column("question_type", form_question_type, nullable=False),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("answer_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(["visit_id"], ["visits.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("visit_id", "question_key", name="uq_visit_form_answer_visit_question"),
    )

    op.execute(
        f"""
        INSERT INTO visit_form_templates (id, name, description, is_active, is_default)
        VALUES (
            '{TEMPLATE_ID}',
            'Jackfruit Farmer Field Visit Report',
            'Monitoring and assessing the conditions of established jackfruit farms and farmer needs.',
            true,
            true
        )
        """
    )

    questions = [
        (
            "00000001-0000-4000-8000-000000000001",
            "visit_metadata",
            "section_header",
            "Visit Information",
            0,
            False,
            None,
            None,
        ),
        (
            "00000002-0000-4000-8000-000000000002",
            "tree_health",
            "single_choice",
            "General Health Assessment of Trees (Overall Canopy and Leaf Quality)",
            10,
            True,
            None,
            None,
        ),
        (
            "00000003-0000-4000-8000-000000000003",
            "pests_diseases",
            "multi_choice",
            "Observed Pest or Disease Presence",
            20,
            True,
            None,
            None,
        ),
        (
            "00000004-0000-4000-8000-000000000004",
            "infrastructure_matrix",
            "matrix",
            "Farm Infrastructure Condition (Irrigation, Fencing, Storage)",
            30,
            True,
            _matrix_config(),
            None,
        ),
        (
            "00000005-0000-4000-8000-000000000005",
            "agronomic_adoption",
            "rating_scale",
            "Rate the Farmer''s adoption of recommended agronomic practices (Pruning, Fertilization, Pest Management)",
            40,
            True,
            _rating_config(),
            None,
        ),
        (
            "00000006-0000-4000-8000-000000000006",
            "assistance_needed",
            "single_choice",
            "Does the farmer require immediate assistance or further training?",
            50,
            True,
            None,
            None,
        ),
        (
            "00000007-0000-4000-8000-000000000007",
            "harvest_schedule_expectations",
            "textarea",
            "Farmer''s Current Harvesting Schedule and Yield Expectations",
            60,
            False,
            None,
            None,
        ),
        (
            "00000008-0000-4000-8000-000000000008",
            "action_plan",
            "textarea",
            "Action Plan/Recommendations based on the visit (Internal Use)",
            80,
            False,
            None,
            None,
        ),
    ]

    for qid, key, qtype, label, sort_order, required, config, help_text in questions:
        config_sql = f"'{config}'::jsonb" if config else "NULL"
        help_sql = f"'{help_text}'" if help_text else "NULL"
        op.execute(
            f"""
            INSERT INTO visit_form_questions
                (id, template_id, question_key, label, help_text, question_type, sort_order, is_required, config)
            VALUES
                ('{qid}', '{TEMPLATE_ID}', '{key}', '{label}', {help_sql}, '{qtype}', {sort_order}, {str(required).lower()}, {config_sql})
            """
        )

    options = {
        "00000002-0000-4000-8000-000000000002": [
            ("excellent", "Excellent (Vibrant, dense canopy)", 1),
            ("good", "Good (Minor issues, full growth)", 2),
            ("fair", "Fair (Visible stress, moderate defoliation)", 3),
            ("poor", "Poor (Severe disease/pest damage, stunted growth)", 4),
        ],
        "00000003-0000-4000-8000-000000000003": [
            ("hairy_caterpillar", "Hairy Caterpillar", 1),
            ("stem_borer", "Stem Borer", 2),
            ("mealybugs", "Mealybugs", 3),
            ("aphids", "Aphids", 4),
            ("fruit_rot", "Fruit Rot", 5),
            ("die_back", "Die Back", 6),
            ("rust", "Rust", 7),
            ("leaf_spot", "Leaf Spot", 8),
            ("no_major_issues", "No major issues observed", 9),
        ],
        "00000006-0000-4000-8000-000000000006": [
            ("critical_intervention", "Yes, critical immediate intervention needed", 1),
            ("follow_up_training", "Yes, follow-up training session recommended", 2),
            ("no_assistance", "No, farm is operating smoothly", 3),
        ],
    }

    for question_id, opts in options.items():
        for value, label, sort_order in opts:
            option_id = str(uuid.uuid4())
            safe_label = label.replace("'", "''")
            op.execute(
                f"""
                INSERT INTO visit_form_question_options (id, question_id, value, label, sort_order)
                VALUES ('{option_id}', '{question_id}', '{value}', '{safe_label}', {sort_order})
                """
            )


def downgrade() -> None:
    op.drop_table("visit_form_answers")
    op.drop_table("visit_form_question_options")
    op.drop_table("visit_form_questions")
    op.drop_table("visit_form_templates")
    op.execute("DROP TYPE IF EXISTS form_question_type")
