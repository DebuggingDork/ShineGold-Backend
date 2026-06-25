import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import VisitStatus


class Visit(Base):
    __tablename__ = "visits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("farms.id"), nullable=False)
    executive_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    status: Mapped[VisitStatus] = mapped_column(
        Enum(VisitStatus, name="visit_status"), default=VisitStatus.IN_PROGRESS, nullable=False
    )

    checkin_lat: Mapped[float] = mapped_column(Float, nullable=False)
    checkin_lng: Mapped[float] = mapped_column(Float, nullable=False)
    checkin_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    checkout_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    checkout_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    checkout_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)

    text_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    voice_note_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # relationships
    farm = relationship("Farm", back_populates="visits")
    executive = relationship("User", back_populates="visits")
    photos = relationship("VisitPhoto", back_populates="visit", cascade="all, delete-orphan")
    mcq_answers = relationship("VisitMcqAnswer", back_populates="visit", cascade="all, delete-orphan")


class VisitPhoto(Base):
    __tablename__ = "visit_photos"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    visit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=False)
    photo_url: Mapped[str] = mapped_column(String(500), nullable=False)
    captured_lat: Mapped[float] = mapped_column(Float, nullable=False)
    captured_lng: Mapped[float] = mapped_column(Float, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    visit = relationship("Visit", back_populates="photos")


class VisitMcqAnswer(Base):
    __tablename__ = "visit_mcq_answers"
    __table_args__ = (UniqueConstraint("visit_id", "question_key", name="uq_visit_mcq_answers_visit_question"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    visit_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("visits.id"), nullable=False)
    question_key: Mapped[str] = mapped_column(String(100), nullable=False)
    answer: Mapped[str] = mapped_column(String(500), nullable=False)

    visit = relationship("Visit", back_populates="mcq_answers")