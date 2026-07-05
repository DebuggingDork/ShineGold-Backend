import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import FarmStatus, Gender


class FarmerCreate(BaseModel):
    name: str
    mobile_number: str
    gender: Gender
    age: int
    photo_url: str | None = None


class FarmerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    mobile_number: str
    gender: Gender
    age: int
    photo_url: str | None = None


class FarmCreate(BaseModel):
    name: str
    location_lat: float
    location_lng: float
    location_address: str | None = None
    crop: str
    harvest_type: str
    harvest_date: date
    total_acres: float
    boundary_geojson: dict | None = None
    photos: list[str] | None = None
    farmer: FarmerCreate


class FarmCreateOut(BaseModel):
    id: uuid.UUID
    name: str
    status: FarmStatus
    farmer_id: uuid.UUID
    created_at: datetime


class FarmerListSummary(BaseModel):
    name: str
    mobile_number: str
    photo_url: str | None = None


class FarmListItem(BaseModel):
    id: uuid.UUID
    name: str
    location_address: str | None = None
    distance_km: float | None = None
    farmer: FarmerListSummary | None = None
    last_visited: datetime | None = None
    status: FarmStatus


class FarmAssignUpdate(BaseModel):
    executive_id: uuid.UUID


class FarmLocation(BaseModel):
    lat: float
    lng: float
    address: str | None = None


class ExecutiveSummary(BaseModel):
    id: uuid.UUID
    name: str


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
    assigned_executive: ExecutiveSummary | None = None
    farmer: FarmerOut | None = None
    photos: list[str] | None = None
    status: FarmStatus
    visit_logs: list[VisitLogItem] = []


class FarmUpdate(BaseModel):
    assigned_executive_id: uuid.UUID | None = None
    harvest_date: date | None = None