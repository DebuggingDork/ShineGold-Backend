import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_super_admin
from app.core.http import raise_bad_request, raise_conflict, raise_not_found
from app.core.user_helpers import requires_location_setup
from app.models.enums import PasswordResetStatus
from app.models.user import User
from app.schemas.auth import (
    ApproveResetRequest,
    ApproveResetResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    PasswordResetListItem,
    PasswordResetStatusOut,
    RefreshRequest,
    RefreshResponse,
    TokenResponse,
)
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserOut
from app.services.auth_service import AuthError, AuthService
from app.services.password_reset_service import PasswordResetError, PasswordResetService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        user, access_token, refresh_token = await auth_service.login(
            payload.employee_id, payload.password
        )
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserOut.model_validate(user).model_copy(
            update={"requires_location_setup": requires_location_setup(user)}
        ),
    )


@router.post("/refresh", response_model=RefreshResponse)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    auth_service = AuthService(db)
    try:
        new_access_token = await auth_service.refresh_access_token(payload.refresh_token)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    return RefreshResponse(access_token=new_access_token)


@router.post("/logout")
async def logout(payload: LogoutRequest | None = None):
    # Stateless JWT setup: nothing to invalidate server-side yet.
    # If you later add a token denylist (e.g. in Redis), revoke payload.refresh_token here.
    return {"message": "Logged out successfully"}


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    reset_service = PasswordResetService(db)
    try:
        request = await reset_service.request_reset(payload.employee_id)
        await db.commit()
    except PasswordResetError as e:
        message = str(e)
        if "already pending" in message:
            raise_conflict(message)
        if "not found" in message:
            raise_not_found(message)
        raise_bad_request(message)

    return ForgotPasswordResponse(
        message="Reset request submitted. Await admin approval.",
        request_id=request.id,
    )


@router.get("/password-reset-requests/status", response_model=PasswordResetStatusOut)
async def password_reset_status(
    employee_id: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
):
    """Public status check used by the forgot-password screen while waiting for admin approval."""
    reset_service = PasswordResetService(db)
    return await reset_service.get_status_for_employee(employee_id)


@router.get("/password-reset-requests", response_model=PaginatedResponse[PasswordResetListItem])
async def list_password_reset_requests(
    status: PasswordResetStatus | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    reset_service = PasswordResetService(db)
    items, total = await reset_service.list_requests(
        status=status,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post(
    "/password-reset-requests/{request_id}/approve",
    response_model=ApproveResetResponse,
)
async def approve_password_reset(
    request_id: uuid.UUID,
    payload: ApproveResetRequest,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    reset_service = PasswordResetService(db)
    try:
        request = await reset_service.approve(request_id, payload.temp_password)
        await db.commit()
    except PasswordResetError as e:
        message = str(e)
        if "not found" in message:
            raise_not_found(message)
        raise_bad_request(message)

    return ApproveResetResponse(
        message="Password reset approved",
        request_id=request.id,
    )


@router.post("/change-password")
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.new_password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    auth_service = AuthService(db)
    try:
        await auth_service.change_password(
            current_user, payload.current_password, payload.new_password
        )
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    await db.commit()
    return {"message": "Password updated successfully"}
