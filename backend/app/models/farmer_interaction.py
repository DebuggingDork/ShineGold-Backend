import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import InteractionStatus


class FarmerInteraction(Base):
    """Prospect conversation logged by an executive before full farm onboard."""

    __tablename__ = "farmer_interactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    executive_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    farmer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    land_location: Mapped[str] = mapped_column(String(500), nullable=False)
    acres: Mapped[float] = mapped_column(Float, nullable=False)
    current_crop: Mapped[str] = mapped_column(String(255), nullable=False)
    planned_months: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[InteractionStatus] = mapped_column(
        Enum(
            InteractionStatus,
            name="interaction_status",
            values_callable=lambda enum_cls: [member.name for member in enum_cls],
        ),
        default=InteractionStatus.UNCERTAIN,
        nullable=False,
        index=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    executive = relationship("User", foreign_keys=[executive_id])
