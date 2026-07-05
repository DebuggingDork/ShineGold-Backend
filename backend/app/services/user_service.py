import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import UserRole
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate


class UserServiceError(Exception):
    pass


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def create_executive(self, payload: UserCreate) -> User:
        if payload.role != UserRole.EXECUTIVE:
            raise UserServiceError("Only executive accounts can be created via this endpoint")

        existing = await self.user_repo.get_by_employee_id(payload.employee_id)
        if existing is not None:
            raise UserServiceError("An account with this employee ID already exists")

        user = User(
            employee_id=payload.employee_id,
            name=payload.name,
            password_hash=hash_password(payload.password),
            role=UserRole.EXECUTIVE,
            mobile_number=payload.mobile_number,
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
