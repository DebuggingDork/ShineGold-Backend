import uuid
from datetime import date, datetime
from typing import Literal, Self

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from app.models.enums import FarmStatus, Gender


class FarmerCreate(BaseModel):
    name: str
    mobile_number: str
    gender: Gender
    age: int
    aadhar_number: str | None = None
    photo_url: str | None = None

    @field_validator("aadhar_number")
    @classmethod
    def validate_aadhar(cls, value: str | None) -> str | None:
        if value is None:
            return None
        digits = "".join(ch for ch in value.strip() if ch.isdigit())
        if not digits:
            return None
        if len(digits) != 12:
            raise ValueError("Aadhar number must be exactly 12 digits")
        return digits


class FarmerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    mobile_number: str
    gender: Gender
    age: int
    aadhar_number: str | None = None
    photo_url: str | None = None


class FarmLocation(BaseModel):
    lat: float
    lng: float
    address: str | None = None


class ExecutiveSummary(BaseModel):
    id: uuid.UUID
    name: str


class FarmCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    location_lat: float = Field(validation_alias=AliasChoices("location_lat", "latitude"))
    location_lng: float = Field(validation_alias=AliasChoices("location_lng", "longitude"))
    location_address: str | None = None
    crop: str
    harvest_type: str
    harvest_date: date
    total_acres: float
    plant_count: int | None = Field(default=None, ge=1)
    boundary_geojson: dict | None = None
    photos: list[str] | None = None
    farmer: FarmerCreate


class FarmAdminCreate(FarmCreate):
    """Super admin farm creation with optional direct executive assignment."""

    executive_ids: list[uuid.UUID] = Field(default_factory=list)


class FarmCreateOut(BaseModel):
    id: uuid.UUID
    name: str
    status: FarmStatus
    farmer_id: uuid.UUID
    assigned_executive_ids: list[uuid.UUID] = Field(default_factory=list)
    created_at: datetime


class FarmerListSummary(BaseModel):
    name: str
    mobile_number: str
    aadhar_number: str | None = None
    photo_url: str | None = None


class FarmListItem(BaseModel):
    id: uuid.UUID
    name: str
    location_address: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    location: FarmLocation | None = None
    distance_km: float | None = None
    farmer: FarmerListSummary | None = None
    last_visited: datetime | None = None
    harvest_date: date
    harvest_type: str
    crop: str
    total_acres: float
    status: FarmStatus
    visit_cooldown_days: int
    next_visit_available_at: datetime | None = None
    onboarded_by: ExecutiveSummary | None = None
    assigned_executive_id: uuid.UUID | None = None
    assigned_executive_name: str | None = None
    assigned_executives: list[ExecutiveSummary] = Field(default_factory=list)


class FarmAssignUpdate(BaseModel):
    executive_ids: list[uuid.UUID] = Field(default_factory=list)
    executive_id: uuid.UUID | None = None
    mode: Literal["replace", "add", "remove"] = "replace"

    @model_validator(mode="after")
    def normalize_executive_ids(self) -> Self:
        if not self.executive_ids and self.executive_id is not None:
            self.executive_ids = [self.executive_id]
        if self.mode in ("add", "remove") and not self.executive_ids:
            raise ValueError("executive_ids is required for add/remove mode")
        return self


class FarmAssignOut(BaseModel):
    farm_id: uuid.UUID
    assigned_executive_ids: list[uuid.UUID]


class FarmInvitationItem(BaseModel):
    id: uuid.UUID
    name: str
    location_address: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    location: FarmLocation | None = None
    distance_km: float
    farmer: FarmerListSummary | None = None
    status: FarmStatus
    assignment_radius_km: float


class FarmAcceptOut(BaseModel):
    farm_id: uuid.UUID
    assigned_executive_ids: list[uuid.UUID]
    distance_km: float


class VisitLogItem(BaseModel):
    visit_id: uuid.UUID
    date: date
    duration_seconds: int | None = None
    report: str | None = None
    photos: list[str] = []
    voice_note: str | None = None
    visited_by: ExecutiveSummary


class FarmDetailOut(BaseModel):
    id: uuid.UUID
    name: str
    harvest_type: str
    harvest_date: date
    crop: str
    location: FarmLocation
    boundary_geojson: dict | None = None
    total_acres: float
    plant_count: int | None = None
    assigned_executives: list[ExecutiveSummary] = Field(default_factory=list)
    farmer: FarmerOut | None = None
    photos: list[str] | None = None
    status: FarmStatus
    visit_cooldown_days: int
    next_visit_available_at: datetime | None = None
    visit_logs: list[VisitLogItem] = []

    @computed_field
    @property
    def assigned_executive_id(self) -> uuid.UUID | None:
        return self.assigned_executives[0].id if self.assigned_executives else None

    @computed_field
    @property
    def assigned_executive_name(self) -> str | None:
        return self.assigned_executives[0].name if self.assigned_executives else None

    @computed_field
    @property
    def assigned_executive(self) -> ExecutiveSummary | None:
        return self.assigned_executives[0] if self.assigned_executives else None


class FarmUpdate(BaseModel):
    harvest_date: date | None = None


class HarvestDateUpdate(BaseModel):
    harvest_date: date
    reason: str | None = Field(default=None, max_length=500)


class HarvestDateChangeOut(BaseModel):
    id: uuid.UUID
    farm_id: uuid.UUID
    old_date: date
    new_date: date
    changed_by_id: uuid.UUID
    changed_by_name: str
    reason: str | None = None
    changed_at: datetime


class HarvestDateUpdateOut(BaseModel):
    farm_id: uuid.UUID
    harvest_date: date
    change: HarvestDateChangeOut
