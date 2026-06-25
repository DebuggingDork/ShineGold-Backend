import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole


class UserBase(BaseModel):
    employee_id: str
    name: str
    role: UserRole


class UserCreate(BaseModel):
    employee_id: str
    name: str
    password: str
    mobile_number: str | None = None
    role: UserRole = UserRole.EXECUTIVE


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: str
    name: str
    role: UserRole
    profile_photo_url: str | None = None
    address: str | None = None
    home_lat: float | None = None
    home_lng: float | None = None
    mobile_number: str | None = None
    is_blocked: bool


class UserUpdateMe(BaseModel):
    name: str | None = None
    address: str | None = None
    home_lat: float | None = None
    home_lng: float | None = None
    mobile_number: str | None = None
    profile_photo_url: str | None = None


class UserBlockUpdate(BaseModel):
    is_blocked: bool


class UserStats(BaseModel):
    total_farms_visited: int
    onboarding_farms_count: int


class UserMeOut(UserOut):
    stats: UserStats