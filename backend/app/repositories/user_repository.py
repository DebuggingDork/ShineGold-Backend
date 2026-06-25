import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_employee_id(self, employee_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.employee_id == employee_id))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def list_executives(
        self,
        search: str | None = None,
        is_blocked: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        from app.models.enums import UserRole

        query = select(User).where(User.role == UserRole.EXECUTIVE)

        if search:
            query = query.where(User.name.ilike(f"%{search}%"))
        if is_blocked is not None:
            query = query.where(User.is_blocked == is_blocked)

        count_query = select(User.id).where(User.role == UserRole.EXECUTIVE)
        if search:
            count_query = count_query.where(User.name.ilike(f"%{search}%"))
        if is_blocked is not None:
            count_query = count_query.where(User.is_blocked == is_blocked)

        total_result = await self.db.execute(count_query)
        total = len(total_result.scalars().all())

        query = query.offset((page - 1) * page_size).limit(page_size)
        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def update(self, user: User) -> User:
        await self.db.flush()
        await self.db.refresh(user)
        return user