import uuid
from datetime import date, datetime
from typing import Literal

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import inspect as orm_inspect
from sqlalchemy.orm import selectinload

from app.core.geo import haversine_km
from app.models.enums import FarmStatus, VisitStatus
from app.models.farm import Farm, Farmer
from app.models.farm_executive_assignment import FarmExecutiveAssignment
from app.models.harvest_date_history import HarvestDateHistory
from app.models.visit import Visit
from app.schemas.farm import (
    ExecutiveSummary,
    FarmCreate,
    FarmDetailOut,
    FarmLocation,
    FarmerListSummary,
    FarmerOut,
    HarvestDateChangeOut,
    VisitLogItem,
)


class FarmRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _farm_load_options():
        return (
            selectinload(Farm.farmer),
            selectinload(Farm.executive_assignments).selectinload(
                FarmExecutiveAssignment.executive
            ),
            selectinload(Farm.visits).selectinload(Visit.executive),
            selectinload(Farm.visits).selectinload(Visit.photos),
        )

    @staticmethod
    def is_executive_assigned(farm: Farm, executive_id: uuid.UUID) -> bool:
        return any(
            assignment.executive_id == executive_id
            for assignment in farm.executive_assignments
        )

    @staticmethod
    def assigned_executive_ids(farm: Farm) -> list[uuid.UUID]:
        return [assignment.executive_id for assignment in farm.executive_assignments]

    async def list_assigned_executive_ids(self, farm_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self.db.execute(
            select(FarmExecutiveAssignment.executive_id).where(
                FarmExecutiveAssignment.farm_id == farm_id
            )
        )
        return list(result.scalars().all())

    async def create(
        self,
        payload: FarmCreate,
        *,
        onboarded_by: uuid.UUID | None,
        executive_ids: list[uuid.UUID] | None = None,
        assigned_by: uuid.UUID | None = None,
        assign_onboarder: bool = True,
    ) -> tuple[Farm, Farmer]:
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

        if executive_ids:
            await self.set_executive_assignments(
                farm,
                executive_ids,
                assigned_by=assigned_by,
                mode="replace",
            )
        elif assign_onboarder and onboarded_by is not None:
            await self.add_executive_assignment(
                farm,
                onboarded_by,
                assigned_by=onboarded_by,
            )

        await self.db.refresh(farm)
        await self.db.refresh(farmer)
        return farm, farmer

    async def add_executive_assignment(
        self,
        farm: Farm,
        executive_id: uuid.UUID,
        *,
        assigned_by: uuid.UUID | None = None,
    ) -> Farm:
        existing = await self.db.execute(
            select(FarmExecutiveAssignment.id).where(
                FarmExecutiveAssignment.farm_id == farm.id,
                FarmExecutiveAssignment.executive_id == executive_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            return farm

        self.db.add(
            FarmExecutiveAssignment(
                farm_id=farm.id,
                executive_id=executive_id,
                assigned_by=assigned_by,
            )
        )
        await self.db.flush()
        await self.db.refresh(farm)
        return farm

    async def set_executive_assignments(
        self,
        farm: Farm,
        executive_ids: list[uuid.UUID],
        *,
        assigned_by: uuid.UUID | None = None,
        mode: Literal["replace", "add", "remove"] = "replace",
    ) -> Farm:
        unique_ids = list(dict.fromkeys(executive_ids))
        current_ids = set(await self.list_assigned_executive_ids(farm.id))

        if mode == "replace":
            target_ids = set(unique_ids)
            to_remove = current_ids - target_ids
            to_add = target_ids - current_ids
        elif mode == "add":
            to_remove: set[uuid.UUID] = set()
            to_add = set(unique_ids) - current_ids
        else:
            to_remove = set(unique_ids) & current_ids
            to_add = set()

        if to_remove:
            await self.db.execute(
                delete(FarmExecutiveAssignment).where(
                    FarmExecutiveAssignment.farm_id == farm.id,
                    FarmExecutiveAssignment.executive_id.in_(to_remove),
                )
            )

        for executive_id in to_add:
            self.db.add(
                FarmExecutiveAssignment(
                    farm_id=farm.id,
                    executive_id=executive_id,
                    assigned_by=assigned_by,
                )
            )

        await self.db.flush()
        await self.db.refresh(farm)
        return farm

    async def get_by_id(self, farm_id: uuid.UUID) -> Farm | None:
        result = await self.db.execute(
            select(Farm).where(Farm.id == farm_id).options(*self._farm_load_options())
        )
        return result.scalar_one_or_none()

    async def update(self, farm: Farm, **fields) -> Farm:
        for key, value in fields.items():
            setattr(farm, key, value)
        await self.db.flush()
        await self.db.refresh(farm)
        return farm

    async def update_harvest_date(
        self,
        farm: Farm,
        *,
        new_date: date,
        changed_by: uuid.UUID,
        reason: str | None = None,
    ) -> HarvestDateHistory:
        """Update harvest_date and append an audit row in the same transaction."""
        if farm.harvest_date == new_date:
            raise ValueError("Harvest date is unchanged")

        old_date = farm.harvest_date
        farm.harvest_date = new_date
        entry = HarvestDateHistory(
            farm_id=farm.id,
            old_date=old_date,
            new_date=new_date,
            changed_by=changed_by,
            reason=(reason.strip() if reason and reason.strip() else None),
        )
        self.db.add(entry)
        await self.db.flush()
        await self.db.refresh(entry)
        await self.db.refresh(farm)
        return entry

    async def list_harvest_date_history(
        self,
        farm_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[HarvestDateHistory], int]:
        filters = [HarvestDateHistory.farm_id == farm_id]
        count_result = await self.db.execute(
            select(func.count()).select_from(HarvestDateHistory).where(*filters)
        )
        total = count_result.scalar_one()
        result = await self.db.execute(
            select(HarvestDateHistory)
            .where(*filters)
            .options(selectinload(HarvestDateHistory.changed_by_user))
            .order_by(HarvestDateHistory.changed_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return list(result.scalars().all()), total

    @staticmethod
    def to_harvest_date_change(entry: HarvestDateHistory) -> HarvestDateChangeOut:
        changer = entry.changed_by_user
        return HarvestDateChangeOut(
            id=entry.id,
            farm_id=entry.farm_id,
            old_date=entry.old_date,
            new_date=entry.new_date,
            changed_by_id=entry.changed_by,
            changed_by_name=changer.name if changer is not None else "Unknown",
            reason=entry.reason,
            changed_at=entry.changed_at,
        )

    async def transfer_assigned_farms(
        self,
        from_executive_id: uuid.UUID,
        to_executive_id: uuid.UUID,
    ) -> list[uuid.UUID]:
        result = await self.db.execute(
            select(FarmExecutiveAssignment).where(
                FarmExecutiveAssignment.executive_id == from_executive_id
            )
        )
        assignments = list(result.scalars().all())
        farm_ids: list[uuid.UUID] = []
        for assignment in assignments:
            farm_ids.append(assignment.farm_id)
            duplicate = await self.db.execute(
                select(FarmExecutiveAssignment.id).where(
                    FarmExecutiveAssignment.farm_id == assignment.farm_id,
                    FarmExecutiveAssignment.executive_id == to_executive_id,
                )
            )
            if duplicate.scalar_one_or_none() is not None:
                await self.db.delete(assignment)
            else:
                assignment.executive_id = to_executive_id
        if farm_ids:
            await self.db.flush()
        return farm_ids

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

        base_query = select(Farm).options(
            selectinload(Farm.farmer),
            selectinload(Farm.executive_assignments).selectinload(
                FarmExecutiveAssignment.executive
            ),
        )
        count_query = select(func.count(func.distinct(Farm.id)))

        filters = []
        if harvest_status is not None:
            filters.append(Farm.status == harvest_status)

        needs_farmer_join = bool(search)
        needs_assignment_join = assigned_to is not None

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

        if needs_assignment_join:
            base_query = base_query.join(
                FarmExecutiveAssignment,
                FarmExecutiveAssignment.farm_id == Farm.id,
            )
            if not needs_farmer_join:
                count_query = count_query.select_from(Farm).join(
                    FarmExecutiveAssignment,
                    FarmExecutiveAssignment.farm_id == Farm.id,
                )
            filters.append(FarmExecutiveAssignment.executive_id == assigned_to)

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
                    haversine_km(lat, lng, farm.location_lat, farm.location_lng), 1
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

    async def list_unassigned_within_radius(
        self,
        *,
        home_lat: float,
        home_lng: float,
        radius_km: float,
        display_lat: float | None = None,
        display_lng: float | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[tuple[Farm, float]], int]:
        distance_lat = display_lat if display_lat is not None else home_lat
        distance_lng = display_lng if display_lng is not None else home_lng

        assigned_farm_ids = select(FarmExecutiveAssignment.farm_id).distinct()
        result = await self.db.execute(
            select(Farm)
            .where(Farm.id.not_in(assigned_farm_ids))
            .options(selectinload(Farm.farmer))
            .order_by(Farm.created_at.desc())
        )
        farms = list(result.scalars().all())

        within_radius: list[tuple[Farm, float]] = []
        for farm in farms:
            coverage_distance = round(
                haversine_km(home_lat, home_lng, farm.location_lat, farm.location_lng), 1
            )
            if coverage_distance <= radius_km:
                display_distance = round(
                    haversine_km(distance_lat, distance_lng, farm.location_lat, farm.location_lng),
                    1,
                )
                within_radius.append((farm, display_distance))

        within_radius.sort(key=lambda item: item[1])
        total = len(within_radius)
        offset = (page - 1) * page_size
        return within_radius[offset : offset + page_size], total

    @staticmethod
    def _loaded_executive_assignments(farm: Farm) -> list:
        if "executive_assignments" in orm_inspect(farm).unloaded:
            return []
        return list(farm.executive_assignments or [])

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

        assigned_executives = [
            ExecutiveSummary(
                id=assignment.executive.id,
                name=assignment.executive.name,
            )
            for assignment in FarmRepository._loaded_executive_assignments(farm)
            if assignment.executive is not None
        ]
        primary_executive = assigned_executives[0] if assigned_executives else None
        location = FarmLocation(
            lat=farm.location_lat,
            lng=farm.location_lng,
            address=farm.location_address,
        )

        return {
            "id": farm.id,
            "name": farm.name,
            "location_address": farm.location_address,
            "location_lat": farm.location_lat,
            "location_lng": farm.location_lng,
            "location": location,
            "distance_km": distance_km,
            "farmer": farmer_summary,
            "last_visited": last_visited,
            "status": farm.status,
            "assigned_executives": assigned_executives,
            "assigned_executive_id": primary_executive.id if primary_executive else None,
            "assigned_executive_name": primary_executive.name if primary_executive else None,
        }

    @staticmethod
    def to_detail(farm: Farm) -> FarmDetailOut:
        assigned_executives = [
            ExecutiveSummary(
                id=assignment.executive.id,
                name=assignment.executive.name,
            )
            for assignment in farm.executive_assignments
        ]

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
            assigned_executives=assigned_executives,
            farmer=farmer,
            photos=farm.photos,
            status=farm.status,
            visit_logs=visit_logs,
        )
