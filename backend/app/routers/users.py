from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_super_admin
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.common import PaginatedResponse
from app.schemas.user import UserListItem, UserMeOut, UserUpdateMe

router = APIRouter(prefix="/api/v1/users", tags=["users"])


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
    return UserMeOut.model_validate(current_user).model_copy(update={"stats": stats})


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
    return UserMeOut.model_validate(current_user).model_copy(update={"stats": stats})
