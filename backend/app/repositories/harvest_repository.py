import calendar
from collections import defaultdict
from datetime import date, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import UserRole
from app.models.farm import Farm
from app.models.farm_executive_assignment import FarmExecutiveAssignment
from app.models.user import User
from app.schemas.harvest import (
    HarvestCalendarOut,
    HarvestDayGroup,
    HarvestFarmSummary,
    HarvestReminderItem,
    HarvestRemindersOut,
)


class HarvestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _month_bounds(month: str) -> tuple[date, date]:
        year_str, month_str = month.split("-", 1)
        year = int(year_str)
        mon = int(month_str)
        last_day = calendar.monthrange(year, mon)[1]
        return date(year, mon, 1), date(year, mon, last_day)

    async def get_calendar(
        self,
        *,
        month: str | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> HarvestCalendarOut:
        if month is not None:
            date_from, date_to = self._month_bounds(month)
        elif date_from is None or date_to is None:
            raise ValueError("Provide either month (YYYY-MM) or both date_from and date_to")

        result = await self.db.execute(
            select(Farm)
            .where(
                and_(
                    Farm.harvest_date >= date_from,
                    Farm.harvest_date <= date_to,
                )
            )
            .order_by(Farm.harvest_date.asc(), Farm.name.asc())
        )
        farms = list(result.scalars().all())

        grouped: dict[date, list[HarvestFarmSummary]] = defaultdict(list)
        for farm in farms:
            grouped[farm.harvest_date].append(
                HarvestFarmSummary(
                    id=farm.id,
                    name=farm.name,
                    crop=farm.crop,
                    harvest_type=farm.harvest_type,
                )
            )

        harvests = [
            HarvestDayGroup(date=harvest_date, farms=grouped[harvest_date])
            for harvest_date in sorted(grouped)
        ]
        return HarvestCalendarOut(harvests=harvests)

    async def list_reminders(
        self,
        *,
        user: User,
        days_before: int = 5,
        horizon_days: int = 90,
    ) -> HarvestRemindersOut:
        today = date.today()
        date_to = today + timedelta(days=horizon_days)

        if user.role == UserRole.SUPER_ADMIN:
            query = (
                select(Farm)
                .where(
                    and_(
                        Farm.harvest_date >= today,
                        Farm.harvest_date <= date_to,
                    )
                )
                .order_by(Farm.harvest_date.asc(), Farm.name.asc())
            )
        elif user.role == UserRole.EXECUTIVE:
            query = (
                select(Farm)
                .join(
                    FarmExecutiveAssignment,
                    FarmExecutiveAssignment.farm_id == Farm.id,
                )
                .where(
                    and_(
                        FarmExecutiveAssignment.executive_id == user.id,
                        Farm.harvest_date >= today,
                        Farm.harvest_date <= date_to,
                    )
                )
                .order_by(Farm.harvest_date.asc(), Farm.name.asc())
            )
        else:
            return HarvestRemindersOut(days_before=days_before, items=[])

        result = await self.db.execute(query)
        farms = list(result.scalars().unique().all())

        items: list[HarvestReminderItem] = []
        for farm in farms:
            remind_on = farm.harvest_date - timedelta(days=days_before)
            items.append(
                HarvestReminderItem(
                    farm_id=farm.id,
                    farm_name=farm.name,
                    crop=farm.crop,
                    harvest_type=farm.harvest_type,
                    harvest_date=farm.harvest_date,
                    remind_on=remind_on,
                    days_until_harvest=(farm.harvest_date - today).days,
                )
            )

        return HarvestRemindersOut(days_before=days_before, items=items)
