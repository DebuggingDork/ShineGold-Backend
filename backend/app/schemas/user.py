import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, AliasChoices

from app.models.enums import FarmStatus, UserRole, VisitStatus


class UserBase(BaseModel):
    employee_id: str
    name: str
    role: UserRole


class UserCreate(BaseModel):
    """Create an executive. employee_id is optional — when omitted the server
    assigns the next EXEC### in sequence."""

    employee_id: str | None = None
    name: str
    address: str
    password: str
    mobile_number: str | None = None
    role: UserRole = UserRole.EXECUTIVE


class UserCreateOut(BaseModel):
    id: uuid.UUID
    employee_id: str
    name: str
    role: UserRole


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
    requires_location_setup: bool = False


class UserUpdateMe(BaseModel):
    name: str | None = None
    address: str | None = None
    home_lat: float | None = None
    home_lng: float | None = None
    mobile_number: str | None = None
    profile_photo_url: str | None = None


class UserBlockUpdate(BaseModel):
    is_blocked: bool


class UserBlockOut(BaseModel):
    id: uuid.UUID
    is_blocked: bool


class UserStats(BaseModel):
    total_farms_visited: int
    onboarding_farms_count: int


class UserMeOut(UserOut):
    stats: UserStats


class UserLocationSetup(BaseModel):
    home_lat: float = Field(validation_alias=AliasChoices("home_lat", "latitude"))
    home_lng: float = Field(validation_alias=AliasChoices("home_lng", "longitude"))
    address: str | None = None

    model_config = ConfigDict(populate_by_name=True)


class UserListItem(BaseModel):
    id: uuid.UUID
    employee_id: str
    name: str
    profile_photo_url: str | None = None
    mobile_number: str | None = None
    is_blocked: bool
    total_farms_visited: int
    farms_assigned_count: int


class UserVisitHistoryItem(BaseModel):
    visit_id: uuid.UUID
    farm_name: str
    date: date
    status: VisitStatus


class UserAssignedFarmItem(BaseModel):
    farm_id: uuid.UUID
    farm_name: str
    status: FarmStatus


class UserDetailOut(BaseModel):
    id: uuid.UUID
    employee_id: str
    name: str
    mobile_number: str | None = None
    profile_photo_url: str | None = None
    is_blocked: bool
    visit_history: list[UserVisitHistoryItem] = []
    assigned_farms: list[UserAssignedFarmItem] = []


class FarmTransferRequest(BaseModel):
    to_executive_id: uuid.UUID


class FarmTransferOut(BaseModel):
    from_executive_id: uuid.UUID
    to_executive_id: uuid.UUID
    farms_transferred: int
    farm_ids: list[uuid.UUID]


class BulkImportRowError(BaseModel):
    row: int
    employee_id: str | None = None
    reason: str


class BulkImportedUser(BaseModel):
    id: uuid.UUID
    employee_id: str
    name: str
    default_password: str


class BulkImportOut(BaseModel):
    created: int
    skipped: int
    errors: list[BulkImportRowError]
    users: list[BulkImportedUser]