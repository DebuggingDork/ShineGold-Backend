from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserMeOut, UserUpdateMe

router = APIRouter(prefix="/api/v1/users", tags=["users"])


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
