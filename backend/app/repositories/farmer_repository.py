import uuid

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.farm import Farmer
from app.schemas.farmer import FarmerDetailOut, FarmerFarmSummary, FarmerListItem


class FarmerRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_farmers(
        self,
        *,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Farmer], int]:
        filters = []
        if search:
            filters.append(
                or_(
                    Farmer.name.ilike(f"%{search}%"),
                    Farmer.mobile_number.ilike(f"%{search}%"),
                )
            )

        base_query = select(Farmer).order_by(Farmer.name.asc())
        count_query = select(func.count()).select_from(Farmer)

        if filters:
            base_query = base_query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        result = await self.db.execute(
            base_query.offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_by_id(self, farmer_id: uuid.UUID) -> Farmer | None:
        result = await self.db.execute(
            select(Farmer)
            .where(Farmer.id == farmer_id)
            .options(selectinload(Farmer.farm))
        )
        return result.scalar_one_or_none()

    @staticmethod
    def to_list_item(farmer: Farmer) -> FarmerListItem:
        return FarmerListItem(
            id=farmer.id,
            name=farmer.name,
            mobile_number=farmer.mobile_number,
            photo_url=farmer.photo_url,
            farms_count=1,
        )

    @staticmethod
    def to_detail(farmer: Farmer) -> FarmerDetailOut:
        farms: list[FarmerFarmSummary] = []
        if farmer.farm is not None:
            farms.append(
                FarmerFarmSummary(
                    id=farmer.farm.id,
                    name=farmer.farm.name,
                    crop=farmer.farm.crop,
                    status=farmer.farm.status,
                )
            )

        return FarmerDetailOut(
            id=farmer.id,
            name=farmer.name,
            mobile_number=farmer.mobile_number,
            gender=farmer.gender,
            age=farmer.age,
            photo_url=farmer.photo_url,
            farms=farms,
        )
