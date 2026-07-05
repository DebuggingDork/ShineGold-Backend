import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import PasswordResetStatus
from app.schemas.user import UserOut


class LoginRequest(BaseModel):
    employee_id: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LogoutRequest(BaseModel):
    refresh_token: str | None = None


class ForgotPasswordRequest(BaseModel):
    employee_id: str


class ForgotPasswordResponse(BaseModel):
    message: str
    request_id: uuid.UUID


class ApproveResetRequest(BaseModel):
    temp_password: str


class ApproveResetResponse(BaseModel):
    message: str
    request_id: uuid.UUID


class PasswordResetUserSummary(BaseModel):
    id: uuid.UUID
    employee_id: str
    name: str


class PasswordResetListItem(BaseModel):
    id: uuid.UUID
    user: PasswordResetUserSummary
    status: PasswordResetStatus
    requested_at: datetime


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str