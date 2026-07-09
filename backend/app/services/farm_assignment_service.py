import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.geo import haversine_km
from app.models.farm import Farm
from app.models.user import User
from app.repositories.farm_repository import FarmRepository


class FarmAssignmentError(Exception):
    pass


class FarmAssignmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.farm_repo = FarmRepository(db)

    @staticmethod
    def _require_home_location(executive: User) -> tuple[float, float]:
        if executive.home_lat is None or executive.home_lng is None:
            raise FarmAssignmentError(
                "Set your home location before viewing or accepting farm invitations"
            )
        return executive.home_lat, executive.home_lng

    def distance_to_farm(self, executive: User, farm: Farm) -> float:
        home_lat, home_lng = self._require_home_location(executive)
        return haversine_km(home_lat, home_lng, farm.location_lat, farm.location_lng)

    def is_within_assignment_radius(self, executive: User, farm: Farm) -> bool:
        return self.distance_to_farm(executive, farm) <= settings.EXECUTIVE_ASSIGNMENT_RADIUS_KM

    @staticmethod
    def can_visit_farm(executive: User, farm: Farm) -> bool:
        return FarmRepository.is_executive_assigned(farm, executive.id)

    async def list_invitations(
        self,
        executive: User,
        *,
        display_lat: float | None = None,
        display_lng: float | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[tuple[Farm, float]], int]:
        home_lat, home_lng = self._require_home_location(executive)
        return await self.farm_repo.list_unassigned_within_radius(
            home_lat=home_lat,
            home_lng=home_lng,
            radius_km=settings.EXECUTIVE_ASSIGNMENT_RADIUS_KM,
            display_lat=display_lat,
            display_lng=display_lng,
            page=page,
            page_size=page_size,
        )

    async def accept_invitation(
        self,
        executive: User,
        farm_id: uuid.UUID,
    ) -> Farm:
        if executive.is_blocked:
            raise FarmAssignmentError("Blocked executives cannot accept farm invitations")

        farm = await self.farm_repo.get_by_id(farm_id)
        if farm is None:
            raise FarmAssignmentError("Farm not found")

        if FarmRepository.is_executive_assigned(farm, executive.id):
            return farm

        if farm.executive_assignments:
            raise FarmAssignmentError("This farm is already assigned to other executives")

        if not self.is_within_assignment_radius(executive, farm):
            raise FarmAssignmentError(
                f"Farm is outside your coverage area "
                f"({settings.EXECUTIVE_ASSIGNMENT_RADIUS_KM:g} km radius from home)"
            )

        return await self.farm_repo.add_executive_assignment(
            farm,
            executive.id,
            assigned_by=executive.id,
        )

    async def assign_executives(
        self,
        farm: Farm,
        executive_ids: list[uuid.UUID],
        *,
        assigned_by: uuid.UUID,
        mode: str = "replace",
    ) -> Farm:
        if not executive_ids and mode != "replace":
            raise FarmAssignmentError("executive_ids is required for add/remove mode")

        return await self.farm_repo.set_executive_assignments(
            farm,
            executive_ids,
            assigned_by=assigned_by,
            mode=mode,  # type: ignore[arg-type]
        )
