import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import FormQuestionType


class VisitFormTemplate(Base):
    __tablename__ = "visit_form_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    questions = relationship(
        "VisitFormQuestion",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="VisitFormQuestion.sort_order",
    )


class VisitFormQuestion(Base):
    __tablename__ = "visit_form_questions"
    __table_args__ = (
        UniqueConstraint("template_id", "question_key", name="uq_visit_form_question_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    template_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visit_form_templates.id", ondelete="CASCADE"), nullable=False
    )
    question_key: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    help_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    question_type: Mapped[FormQuestionType] = mapped_column(
        Enum(
            FormQuestionType,
            name="form_question_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    config: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    template = relationship("VisitFormTemplate", back_populates="questions")
    options = relationship(
        "VisitFormQuestionOption",
        back_populates="question",
        cascade="all, delete-orphan",
        order_by="VisitFormQuestionOption.sort_order",
    )


class VisitFormQuestionOption(Base):
    __tablename__ = "visit_form_question_options"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visit_form_questions.id", ondelete="CASCADE"), nullable=False
    )
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    question = relationship("VisitFormQuestion", back_populates="options")


class VisitFormAnswer(Base):
    __tablename__ = "visit_form_answers"
    __table_args__ = (
        UniqueConstraint("visit_id", "question_key", name="uq_visit_form_answer_visit_question"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    visit_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("visits.id", ondelete="CASCADE"), nullable=False
    )
    question_key: Mapped[str] = mapped_column(String(100), nullable=False)
    question_label: Mapped[str] = mapped_column(String(500), nullable=False)
    question_type: Mapped[FormQuestionType] = mapped_column(
        Enum(
            FormQuestionType,
            name="form_question_type",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
    )
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    answer_json: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)

    visit = relationship("Visit", back_populates="form_answers")
