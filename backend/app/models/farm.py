import uuid
from datetime import date, datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Date, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import FarmStatus, Gender


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    location_lat: Mapped[float] = mapped_column(Float, nullable=False)
    location_lng: Mapped[float] = mapped_column(Float, nullable=False)
    location_address: Mapped[str | None] = mapped_column(String(500), nullable=True)

    crop: Mapped[str] = mapped_column(String(255), nullable=False)
    harvest_type: Mapped[str] = mapped_column(String(255), nullable=False)
    harvest_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_acres: Mapped[float] = mapped_column(Float, nullable=False)

    boundary_geojson: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    photos: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # list[str] of URLs

    assigned_executive_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    onboarded_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    status: Mapped[FarmStatus] = mapped_column(
        Enum(FarmStatus, name="farm_status"), default=FarmStatus.PENDING_VISIT, nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # relationships
    assigned_executive = relationship("User", back_populates="assigned_farms", foreign_keys=[assigned_executive_id])
    onboarded_by_user = relationship("User", back_populates="onboarded_farms", foreign_keys=[onboarded_by])
    farmer = relationship("Farmer", back_populates="farm", uselist=False, cascade="all, delete-orphan")
    visits = relationship("Visit", back_populates="farm")


class Farmer(Base):
    __tablename__ = "farmers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    farm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("farms.id"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    mobile_number: Mapped[str] = mapped_column(String(20), nullable=False)
    gender: Mapped[Gender] = mapped_column(Enum(Gender, name="gender"), nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    farm = relationship("Farm", back_populates="farmer")