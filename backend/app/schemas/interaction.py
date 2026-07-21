import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import InteractionStatus


class InteractionCreate(BaseModel):
    farmer_name: str = Field(min_length=1, max_length=255)
    phone_number: str = Field(min_length=7, max_length=20)
    land_location: str = Field(min_length=1, max_length=500)
    acres: float = Field(gt=0, le=10000)
    current_crop: str = Field(min_length=1, max_length=255)
    planned_months: int = Field(ge=1, le=60)
    status: InteractionStatus = InteractionStatus.UNCERTAIN
    notes: str | None = Field(default=None, max_length=2000)


class InteractionUpdate(BaseModel):
    farmer_name: str | None = Field(default=None, min_length=1, max_length=255)
    phone_number: str | None = Field(default=None, min_length=7, max_length=20)
    land_location: str | None = Field(default=None, min_length=1, max_length=500)
    acres: float | None = Field(default=None, gt=0, le=10000)
    current_crop: str | None = Field(default=None, min_length=1, max_length=255)
    planned_months: int | None = Field(default=None, ge=1, le=60)
    status: InteractionStatus | None = None
    notes: str | None = Field(default=None, max_length=2000)


class InteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    executive_id: uuid.UUID
    farmer_name: str
    phone_number: str
    land_location: str
    acres: float
    current_crop: str
    planned_months: int
    status: InteractionStatus
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
