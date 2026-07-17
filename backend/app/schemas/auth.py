import uuid
from datetime import datetime

from pydantic import BaseModel, Field

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
    """Admin approval only — executive sets their own password afterward."""

    pass


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


class PasswordResetStatusOut(BaseModel):
    employee_id: str
    status: PasswordResetStatus | None = None
    approved: bool = False
    message: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class AdminChangePasswordRequest(BaseModel):
    new_password: str = Field(min_length=6)
    confirm_password: str = Field(min_length=6)


class SetPasswordAfterResetRequest(BaseModel):
    employee_id: str
    new_password: str
    confirm_password: str