import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import UserRole, VisitStatus
from app.models.farm import Farm
from app.models.user import User
from app.models.visit import Visit
from app.schemas.user import (
    UserAssignedFarmItem,
    UserDetailOut,
    UserStats,
    UserVisitHistoryItem,
)


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

    async def get_user_stats(self, user_id: uuid.UUID) -> UserStats:
        visits_result = await self.db.execute(
            select(func.count())
            .select_from(Visit)
            .where(Visit.executive_id == user_id, Visit.status == VisitStatus.COMPLETED)
        )
        farms_result = await self.db.execute(
            select(func.count()).select_from(Farm).where(Farm.onboarded_by == user_id)
        )
        return UserStats(
            total_farms_visited=visits_result.scalar_one(),
            onboarding_farms_count=farms_result.scalar_one(),
        )

    async def count_assigned_farms(self, executive_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Farm)
            .where(Farm.assigned_executive_id == executive_id)
        )
        return result.scalar_one()

    async def list_executive_items(
        self,
        *,
        search: str | None = None,
        is_blocked: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict], int]:
        executives, total = await self.list_executives(
            search=search,
            is_blocked=is_blocked,
            page=page,
            page_size=page_size,
        )
        items = []
        for executive in executives:
            stats = await self.get_user_stats(executive.id)
            assigned_count = await self.count_assigned_farms(executive.id)
            items.append(
                {
                    "id": executive.id,
                    "employee_id": executive.employee_id,
                    "name": executive.name,
                    "profile_photo_url": executive.profile_photo_url,
                    "mobile_number": executive.mobile_number,
                    "is_blocked": executive.is_blocked,
                    "total_farms_visited": stats.total_farms_visited,
                    "farms_assigned_count": assigned_count,
                }
            )
        return items, total

    async def get_executive_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id, User.role == UserRole.EXECUTIVE)
        )
        return result.scalar_one_or_none()

    async def get_executive_detail(self, user_id: uuid.UUID) -> UserDetailOut | None:
        executive = await self.get_executive_by_id(user_id)
        if executive is None:
            return None

        visits_result = await self.db.execute(
            select(Visit)
            .where(Visit.executive_id == user_id)
            .options(selectinload(Visit.farm))
            .order_by(Visit.checkin_time.desc())
        )
        visits = list(visits_result.scalars().all())

        farms_result = await self.db.execute(
            select(Farm)
            .where(Farm.assigned_executive_id == user_id)
            .order_by(Farm.name.asc())
        )
        farms = list(farms_result.scalars().all())

        return UserRepository.to_detail(executive, visits, farms)

    @staticmethod
    def to_detail(
        executive: User,
        visits: list[Visit],
        farms: list[Farm],
    ) -> UserDetailOut:
        visit_history: list[UserVisitHistoryItem] = []
        for visit in visits:
            visit_time = visit.checkout_time or visit.checkin_time
            visit_history.append(
                UserVisitHistoryItem(
                    visit_id=visit.id,
                    farm_name=visit.farm.name,
                    date=visit_time.date(),
                    status=visit.status,
                )
            )

        assigned_farms = [
            UserAssignedFarmItem(
                farm_id=farm.id,
                farm_name=farm.name,
                status=farm.status,
            )
            for farm in farms
        ]

        return UserDetailOut(
            id=executive.id,
            employee_id=executive.employee_id,
            name=executive.name,
            mobile_number=executive.mobile_number,
            profile_photo_url=executive.profile_photo_url,
            is_blocked=executive.is_blocked,
            visit_history=visit_history,
            assigned_farms=assigned_farms,
        )