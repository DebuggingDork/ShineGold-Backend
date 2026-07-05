import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import VisitStatus
from app.models.visit import Visit


class VisitRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_in_progress_for_executive(self, executive_id: uuid.UUID) -> Visit | None:
        result = await self.db.execute(
            select(Visit).where(
                Visit.executive_id == executive_id,
                Visit.status == VisitStatus.IN_PROGRESS,
            )
        )
        return result.scalar_one_or_none()

    async def create_checkin(
        self,
        farm_id: uuid.UUID,
        executive_id: uuid.UUID,
        checkin_lat: float,
        checkin_lng: float,
    ) -> Visit:
        visit = Visit(
            farm_id=farm_id,
            executive_id=executive_id,
            checkin_lat=checkin_lat,
            checkin_lng=checkin_lng,
            status=VisitStatus.IN_PROGRESS,
        )
        self.db.add(visit)
        await self.db.flush()
        await self.db.refresh(visit)
        return visit
