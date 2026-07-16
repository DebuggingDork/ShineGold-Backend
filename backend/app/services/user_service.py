import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.farm_repository import FarmRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserServiceError(Exception):
    pass


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.farm_repo = FarmRepository(db)

    async def create_executive(self, payload: UserCreate) -> User:
        if payload.role != UserRole.EXECUTIVE:
            raise UserServiceError("Only executive accounts can be created via this endpoint")

        employee_id = (payload.employee_id or "").strip()
        if employee_id:
            existing = await self.user_repo.get_by_employee_id(employee_id)
            if existing is not None:
                raise UserServiceError("An account with this employee ID already exists")
        else:
            # Allocate the next EXEC### with a short retry in case of a race.
            for _ in range(5):
                employee_id = await self.user_repo.next_executive_employee_id()
                existing = await self.user_repo.get_by_employee_id(employee_id)
                if existing is None:
                    break
            else:
                raise UserServiceError("Could not allocate a unique employee ID. Try again.")

        if payload.home_lat is None or payload.home_lng is None:
            raise UserServiceError(
                "home_lat and home_lng are required. Verify the address before creating the executive."
            )

        mobile = (payload.mobile_number or "").strip()
        if not mobile:
            raise UserServiceError("Mobile number is required")
        existing_mobile = await self.user_repo.get_by_mobile_number(mobile)
        if existing_mobile is not None:
            raise UserServiceError("Executive already exists")
        mobile = UserRepository.normalize_mobile(mobile) or mobile

        user = User(
            employee_id=employee_id,
            name=payload.name,
            address=payload.address,
            password_hash=hash_password(payload.password),
            role=UserRole.EXECUTIVE,
            mobile_number=mobile,
            home_lat=payload.home_lat,
            home_lng=payload.home_lng,
        )
        return await self.user_repo.create(user)

    async def get_executive(self, user_id: uuid.UUID) -> User:
        executive = await self.user_repo.get_executive_by_id(user_id)
        if executive is None:
            raise UserServiceError("Executive not found")
        return executive

    async def get_assignable_executive(self, executive_id: uuid.UUID) -> User:
        executive = await self.get_executive(executive_id)
        if executive.is_blocked:
            raise UserServiceError("Cannot assign a blocked executive")
        return executive

    async def set_blocked(self, user_id: uuid.UUID, is_blocked: bool) -> User:
        executive = await self.get_executive(user_id)
        executive.is_blocked = is_blocked
        return await self.user_repo.update(executive)

    async def transfer_farms(
        self,
        from_executive_id: uuid.UUID,
        to_executive_id: uuid.UUID,
    ) -> tuple[uuid.UUID, uuid.UUID, list[uuid.UUID]]:
        if from_executive_id == to_executive_id:
            raise UserServiceError("Cannot transfer farms to the same executive")

        await self.get_executive(from_executive_id)
        await self.get_assignable_executive(to_executive_id)

        farm_ids = await self.farm_repo.transfer_assigned_farms(
            from_executive_id,
            to_executive_id,
        )
        return from_executive_id, to_executive_id, farm_ids

    async def setup_home_location(
        self,
        user: User,
        *,
        home_lat: float,
        home_lng: float,
        address: str | None = None,
    ) -> User:
        if user.role != UserRole.EXECUTIVE:
            raise UserServiceError("Only executives can set a home location")

        user.home_lat = home_lat
        user.home_lng = home_lng
        if address is not None:
            user.address = address
        return await self.user_repo.update(user)
