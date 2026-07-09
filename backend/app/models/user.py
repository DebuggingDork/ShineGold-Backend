import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import PasswordResetStatus, UserRole


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    employee_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), nullable=False)

    profile_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    home_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    home_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    mobile_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # relationships
    onboarded_farms = relationship("Farm", back_populates="onboarded_by_user", foreign_keys="Farm.onboarded_by")
    farm_assignments = relationship(
        "FarmExecutiveAssignment",
        back_populates="executive",
        foreign_keys="FarmExecutiveAssignment.executive_id",
    )
    visits = relationship("Visit", back_populates="executive")
    password_reset_requests = relationship("PasswordResetRequest", back_populates="user")


class PasswordResetRequest(Base):
    __tablename__ = "password_reset_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[PasswordResetStatus] = mapped_column(
        Enum(PasswordResetStatus, name="password_reset_status"),
        default=PasswordResetStatus.PENDING,
        nullable=False,
    )
    temp_password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="password_reset_requests")