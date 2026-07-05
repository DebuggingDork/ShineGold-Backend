from datetime import date, datetime, time, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole, VisitStatus
from app.models.farm import Farm, Farmer
from app.models.user import User
from app.models.visit import Visit
from app.schemas.dashboard import AdminDashboardOut


class DashboardRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _date_start(value: date) -> datetime:
        return datetime.combine(value, time.min, tzinfo=timezone.utc)

    @staticmethod
    def _date_end(value: date) -> datetime:
        return datetime.combine(value, time.max, tzinfo=timezone.utc)

    async def get_admin_stats(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> AdminDashboardOut:
        farm_filters = []
        farmer_filters = []
        visit_filters = [Visit.status == VisitStatus.COMPLETED]

        if date_from is not None:
            start = self._date_start(date_from)
            farm_filters.append(Farm.created_at >= start)
            farmer_filters.append(Farmer.created_at >= start)
            visit_filters.append(Visit.checkin_time >= start)
        if date_to is not None:
            end = self._date_end(date_to)
            farm_filters.append(Farm.created_at <= end)
            farmer_filters.append(Farmer.created_at <= end)
            visit_filters.append(Visit.checkin_time <= end)

        total_farms = await self._count(Farm, farm_filters)
        farmers_onboarded = await self._count(Farmer, farmer_filters)
        total_visits = await self._count(Visit, visit_filters)
        total_executives = await self._count(
            User,
            [User.role == UserRole.EXECUTIVE],
        )

        return AdminDashboardOut(
            total_farms=total_farms,
            total_executives=total_executives,
            total_visits=total_visits,
            farmers_onboarded=farmers_onboarded,
        )

    async def _count(self, model, filters: list) -> int:
        query = select(func.count()).select_from(model)
        if filters:
            query = query.where(*filters)
        result = await self.db.execute(query)
        return result.scalar_one()
