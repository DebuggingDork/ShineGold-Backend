import uuid

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_executive, require_super_admin
from app.core.http import raise_bad_request, raise_not_found
from app.core.user_helpers import requires_location_setup
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.user import (
    BulkImportOut,
    FarmTransferOut,
    FarmTransferRequest,
    UserBlockOut,
    UserBlockUpdate,
    UserCreate,
    UserCreateOut,
    UserDetailOut,
    UserListItem,
    UserLocationSetup,
    UserMeOut,
    UserOut,
    UserUpdateMe,
)
from app.services.bulk_import_service import BulkImportError, BulkImportService
from app.services.user_service import UserService, UserServiceError

router = APIRouter(prefix="/api/v1/users", tags=["users"])


def _build_user_me_out(user: User, stats) -> UserMeOut:
    base = UserOut.model_validate(user, from_attributes=True)
    payload = base.model_dump(exclude={"requires_location_setup"})
    return UserMeOut(
        **payload,
        stats=stats,
        requires_location_setup=requires_location_setup(user),
    )


@router.post("", response_model=UserCreateOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    try:
        created = await user_service.create_executive(payload)
        await db.commit()
    except UserServiceError as e:
        raise_bad_request(str(e))

    return UserCreateOut(
        id=created.id,
        employee_id=created.employee_id,
        name=created.name,
        role=created.role,
    )


@router.get("/bulk-import/template")
async def download_bulk_import_template(
    _current_user: User = Depends(require_super_admin),
):
    content = BulkImportService.build_template_bytes()
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="executive_import_template.xlsx"'},
    )


@router.post("/bulk-import", response_model=BulkImportOut, status_code=status.HTTP_201_CREATED)
async def bulk_import_users(
    file: UploadFile = File(...),
    default_password: str = Form(..., min_length=6),
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    if not file.filename:
        raise_bad_request("Uploaded file must have a filename")

    content = await file.read()
    if not content:
        raise_bad_request("Uploaded file is empty")

    import_service = BulkImportService(db)
    try:
        rows = import_service.parse_upload(content, file.filename)
        result = await import_service.import_executives(rows, default_password)
        await db.commit()
    except BulkImportError as e:
        raise_bad_request(str(e))

    return result


@router.get("", response_model=PaginatedResponse[UserListItem])
async def list_users(
    search: str | None = Query(None),
    is_blocked: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    items, total = await user_repo.list_executive_items(
        search=search,
        is_blocked=is_blocked,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=[UserListItem(**item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/me", response_model=UserMeOut)
async def read_current_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    stats = await user_repo.get_user_stats(current_user.id)
    return _build_user_me_out(current_user, stats)


@router.post("/me/setup-location", response_model=UserMeOut)
async def setup_home_location(
    payload: UserLocationSetup,
    current_user: User = Depends(require_executive),
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    try:
        updated = await user_service.setup_home_location(
            current_user,
            home_lat=payload.home_lat,
            home_lng=payload.home_lng,
            address=payload.address,
        )
        await db.commit()
    except UserServiceError as e:
        raise_bad_request(str(e))

    user_repo = UserRepository(db)
    stats = await user_repo.get_user_stats(updated.id)
    return _build_user_me_out(updated, stats)


@router.patch("/me", response_model=UserMeOut)
async def update_current_user(
    payload: UserUpdateMe,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(current_user, field, value)

    await user_repo.update(current_user)
    await db.commit()

    stats = await user_repo.get_user_stats(current_user.id)
    return _build_user_me_out(current_user, stats)


@router.get("/{user_id}", response_model=UserDetailOut)
async def get_user(
    user_id: uuid.UUID,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    user_repo = UserRepository(db)
    detail = await user_repo.get_executive_detail(user_id)
    if detail is None:
        raise_not_found("Executive not found")
    return detail


@router.patch("/{user_id}/block", response_model=UserBlockOut)
async def block_user(
    user_id: uuid.UUID,
    payload: UserBlockUpdate,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    try:
        executive = await user_service.set_blocked(user_id, payload.is_blocked)
        await db.commit()
    except UserServiceError as e:
        raise_not_found(str(e))

    return UserBlockOut(id=executive.id, is_blocked=executive.is_blocked)


@router.post("/{user_id}/transfer-farms", response_model=FarmTransferOut)
async def transfer_executive_farms(
    user_id: uuid.UUID,
    payload: FarmTransferRequest,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    user_service = UserService(db)
    try:
        from_id, to_id, farm_ids = await user_service.transfer_farms(
            user_id,
            payload.to_executive_id,
        )
        await db.commit()
    except UserServiceError as e:
        raise_bad_request(str(e))

    return FarmTransferOut(
        from_executive_id=from_id,
        to_executive_id=to_id,
        farms_transferred=len(farm_ids),
        farm_ids=farm_ids,
    )
