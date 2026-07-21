import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import InteractionStatus
from app.models.farmer_interaction import FarmerInteraction
from app.schemas.interaction import InteractionCreate, InteractionUpdate


class InteractionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        *,
        executive_id: uuid.UUID,
        data: InteractionCreate,
    ) -> FarmerInteraction:
        row = FarmerInteraction(
            executive_id=executive_id,
            farmer_name=data.farmer_name.strip(),
            phone_number=data.phone_number.strip(),
            land_location=data.land_location.strip(),
            acres=data.acres,
            current_crop=data.current_crop.strip(),
            planned_months=data.planned_months,
            status=data.status,
            notes=data.notes.strip() if data.notes else None,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def list_for_executive(
        self,
        *,
        executive_id: uuid.UUID,
        search: str | None = None,
        status: InteractionStatus | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[FarmerInteraction], int]:
        filters = [FarmerInteraction.executive_id == executive_id]
        if status is not None:
            filters.append(FarmerInteraction.status == status)
        if search:
            term = f"%{search.strip()}%"
            filters.append(
                or_(
                    FarmerInteraction.farmer_name.ilike(term),
                    FarmerInteraction.phone_number.ilike(term),
                    FarmerInteraction.land_location.ilike(term),
                    FarmerInteraction.current_crop.ilike(term),
                )
            )

        where = and_(*filters)
        total = (
            await self.db.execute(
                select(func.count()).select_from(FarmerInteraction).where(where)
            )
        ).scalar_one()

        result = await self.db.execute(
            select(FarmerInteraction)
            .where(where)
            .order_by(FarmerInteraction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, interaction_id: uuid.UUID) -> FarmerInteraction | None:
        result = await self.db.execute(
            select(FarmerInteraction).where(FarmerInteraction.id == interaction_id)
        )
        return result.scalar_one_or_none()

    async def update(
        self,
        row: FarmerInteraction,
        data: InteractionUpdate,
    ) -> FarmerInteraction:
        payload = data.model_dump(exclude_unset=True)
        for key, value in payload.items():
            if isinstance(value, str):
                value = value.strip()
                if key == "notes" and value == "":
                    value = None
            setattr(row, key, value)
        await self.db.commit()
        await self.db.refresh(row)
        return row
