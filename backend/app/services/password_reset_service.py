import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import PasswordResetStatus, UserRole
from app.models.user import PasswordResetRequest
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import PasswordResetListItem, PasswordResetUserSummary


class PasswordResetError(Exception):
    pass


class PasswordResetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.reset_repo = PasswordResetRepository(db)
        self.user_repo = UserRepository(db)

    async def request_reset(self, employee_id: str) -> PasswordResetRequest:
        user = await self.user_repo.get_by_employee_id(employee_id)
        if user is None or user.role != UserRole.EXECUTIVE:
            raise PasswordResetError("No executive account found for this employee ID")
        if user.is_blocked:
            raise PasswordResetError("This account has been blocked. Contact your admin.")

        existing = await self.reset_repo.get_pending_for_user(user.id)
        if existing is not None:
            raise PasswordResetError("A password reset request is already pending for this account")

        return await self.reset_repo.create(user.id)

    async def list_requests(
        self,
        *,
        status: PasswordResetStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PasswordResetListItem], int]:
        requests, total = await self.reset_repo.list_requests(
            status=status,
            page=page,
            page_size=page_size,
        )
        items = [self._to_list_item(request) for request in requests]
        return items, total

    async def approve(self, request_id: uuid.UUID, temp_password: str) -> PasswordResetRequest:
        request = await self.reset_repo.get_by_id(request_id)
        if request is None:
            raise PasswordResetError("Password reset request not found")
        if request.status != PasswordResetStatus.PENDING:
            raise PasswordResetError("Password reset request is no longer pending")

        temp_hash = hash_password(temp_password)
        request.user.password_hash = temp_hash
        await self.user_repo.update(request.user)
        return await self.reset_repo.resolve(
            request,
            status=PasswordResetStatus.APPROVED,
            temp_password_hash=temp_hash,
        )

    @staticmethod
    def _to_list_item(request: PasswordResetRequest) -> PasswordResetListItem:
        return PasswordResetListItem(
            id=request.id,
            user=PasswordResetUserSummary(
                id=request.user.id,
                employee_id=request.user.employee_id,
                name=request.user.name,
            ),
            status=request.status,
            requested_at=request.requested_at,
        )
