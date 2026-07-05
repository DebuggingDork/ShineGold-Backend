import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import FarmStatus, Gender


class FarmerListItem(BaseModel):
    id: uuid.UUID
    name: str
    mobile_number: str
    photo_url: str | None = None
    farms_count: int


class FarmerFarmSummary(BaseModel):
    id: uuid.UUID
    name: str
    crop: str
    status: FarmStatus


class FarmerDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    mobile_number: str
    gender: Gender
    age: int
    photo_url: str | None = None
    farms: list[FarmerFarmSummary] = []
