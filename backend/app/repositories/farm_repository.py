import math
import uuid
from datetime import datetime
from typing import Literal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import FarmStatus, VisitStatus
from app.models.farm import Farm, Farmer
from app.models.visit import Visit
from app.schemas.farm import (
    ExecutiveSummary,
    FarmCreate,
    FarmDetailOut,
    FarmLocation,
    FarmerListSummary,
    FarmerOut,
    VisitLogItem,
)


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    radius_km = 6371.0
    d_lat = math.radians(lat2 - lat1)
    d_lng = math.radians(lng2 - lng1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lng / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


class FarmRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, payload: FarmCreate, onboarded_by: uuid.UUID) -> tuple[Farm, Farmer]:
        farm = Farm(
            name=payload.name,
            location_lat=payload.location_lat,
            location_lng=payload.location_lng,
            location_address=payload.location_address,
            crop=payload.crop,
            harvest_type=payload.harvest_type,
            harvest_date=payload.harvest_date,
            total_acres=payload.total_acres,
            boundary_geojson=payload.boundary_geojson,
            photos=payload.photos,
            onboarded_by=onboarded_by,
            assigned_executive_id=onboarded_by,
            status=FarmStatus.PENDING_VISIT,
        )
        self.db.add(farm)
        await self.db.flush()

        farmer = Farmer(
            farm_id=farm.id,
            name=payload.farmer.name,
            mobile_number=payload.farmer.mobile_number,
            gender=payload.farmer.gender,
            age=payload.farmer.age,
            photo_url=payload.farmer.photo_url,
        )
        self.db.add(farmer)
        await self.db.flush()
        await self.db.refresh(farm)
        await self.db.refresh(farmer)
        return farm, farmer

    async def get_by_id(self, farm_id: uuid.UUID) -> Farm | None:
        result = await self.db.execute(
            select(Farm)
            .where(Farm.id == farm_id)
            .options(
                selectinload(Farm.farmer),
                selectinload(Farm.assigned_executive),
                selectinload(Farm.visits).selectinload(Visit.executive),
                selectinload(Farm.visits).selectinload(Visit.photos),
            )
        )
        return result.scalar_one_or_none()

    async def update(self, farm: Farm, **fields) -> Farm:
        for key, value in fields.items():
            setattr(farm, key, value)
        await self.db.flush()
        await self.db.refresh(farm)
        return farm

    async def list_farms(
        self,
        *,
        lat: float | None = None,
        lng: float | None = None,
        sort: Literal["distance", "farthest"] | None = None,
        harvest_status: FarmStatus | None = None,
        assigned_to: uuid.UUID | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[tuple[Farm, float | None, datetime | None]], int]:
        last_visit_subq = (
            select(
                Visit.farm_id.label("farm_id"),
                func.max(Visit.checkout_time).label("last_visited"),
            )
            .where(Visit.status == VisitStatus.COMPLETED)
            .group_by(Visit.farm_id)
            .subquery()
        )

        base_query = select(Farm).options(selectinload(Farm.farmer))
        count_query = select(func.count(func.distinct(Farm.id)))

        filters = []
        if harvest_status is not None:
            filters.append(Farm.status == harvest_status)
        if assigned_to is not None:
            filters.append(Farm.assigned_executive_id == assigned_to)

        needs_farmer_join = bool(search)
        if needs_farmer_join:
            base_query = base_query.join(Farmer, Farmer.farm_id == Farm.id)
            count_query = count_query.select_from(Farm).join(Farmer, Farmer.farm_id == Farm.id)
            filters.append(
                or_(
                    Farm.name.ilike(f"%{search}%"),
                    Farmer.name.ilike(f"%{search}%"),
                )
            )
        else:
            count_query = count_query.select_from(Farm)

        if filters:
            base_query = base_query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        result = await self.db.execute(base_query)
        farms = list(result.scalars().unique().all())

        farm_ids = [farm.id for farm in farms]
        last_visited_by_farm: dict[uuid.UUID, datetime] = {}
        if farm_ids:
            last_visit_result = await self.db.execute(
                select(last_visit_subq.c.farm_id, last_visit_subq.c.last_visited).where(
                    last_visit_subq.c.farm_id.in_(farm_ids)
                )
            )
            last_visited_by_farm = {
                row.farm_id: row.last_visited for row in last_visit_result.all()
            }

        items: list[tuple[Farm, float | None, datetime | None]] = []
        for farm in farms:
            distance_km = None
            if lat is not None and lng is not None:
                distance_km = round(
                    _haversine_km(lat, lng, farm.location_lat, farm.location_lng), 1
                )
            items.append((farm, distance_km, last_visited_by_farm.get(farm.id)))

        if sort in ("distance", "farthest"):
            if lat is None or lng is None:
                raise ValueError("lat and lng are required when sort is distance or farthest")
            items.sort(
                key=lambda item: item[1] if item[1] is not None else float("inf"),
                reverse=sort == "farthest",
            )
        else:
            items.sort(key=lambda item: item[0].created_at, reverse=True)

        offset = (page - 1) * page_size
        return items[offset : offset + page_size], total

    @staticmethod
    def to_list_item(
        farm: Farm, distance_km: float | None, last_visited: datetime | None
    ) -> dict:
        farmer_summary = None
        if farm.farmer:
            farmer_summary = FarmerListSummary(
                name=farm.farmer.name,
                mobile_number=farm.farmer.mobile_number,
                photo_url=farm.farmer.photo_url,
            )

        return {
            "id": farm.id,
            "name": farm.name,
            "location_address": farm.location_address,
            "distance_km": distance_km,
            "farmer": farmer_summary,
            "last_visited": last_visited,
            "status": farm.status,
        }

    @staticmethod
    def to_detail(farm: Farm) -> FarmDetailOut:
        assigned_executive = None
        if farm.assigned_executive:
            assigned_executive = ExecutiveSummary(
                id=farm.assigned_executive.id,
                name=farm.assigned_executive.name,
            )

        farmer = FarmerOut.model_validate(farm.farmer) if farm.farmer else None

        visit_logs: list[VisitLogItem] = []
        completed_visits = [
            v for v in farm.visits if v.status == VisitStatus.COMPLETED
        ]
        completed_visits.sort(
            key=lambda v: v.checkout_time or v.checkin_time, reverse=True
        )
        for visit in completed_visits:
            visit_date = visit.checkout_time or visit.checkin_time
            visit_logs.append(
                VisitLogItem(
                    visit_id=visit.id,
                    date=visit_date.date(),
                    duration_seconds=visit.duration_seconds,
                    report=visit.text_note,
                    photos=[photo.photo_url for photo in visit.photos],
                    voice_note=visit.voice_note_url,
                    visited_by=ExecutiveSummary(
                        id=visit.executive.id,
                        name=visit.executive.name,
                    ),
                )
            )

        return FarmDetailOut(
            id=farm.id,
            name=farm.name,
            harvest_type=farm.harvest_type,
            harvest_date=farm.harvest_date,
            crop=farm.crop,
            location=FarmLocation(
                lat=farm.location_lat,
                lng=farm.location_lng,
                address=farm.location_address,
            ),
            boundary_geojson=farm.boundary_geojson,
            total_acres=farm.total_acres,
            assigned_executive=assigned_executive,
            farmer=farmer,
            photos=farm.photos,
            status=farm.status,
            visit_logs=visit_logs,
        )
