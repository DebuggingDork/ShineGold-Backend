import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import PasswordResetStatus, UserRole
from app.models.user import PasswordResetRequest, User
from app.repositories.password_reset_repository import PasswordResetRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import PasswordResetListItem, PasswordResetStatusOut, PasswordResetUserSummary


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

        open_approved = await self.reset_repo.get_open_approved_for_user(user.id)
        if open_approved is not None:
            raise PasswordResetError(
                "Your reset is already approved. Set your new password now."
            )

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

    async def get_status_for_employee(self, employee_id: str) -> PasswordResetStatusOut:
        user = await self.user_repo.get_by_employee_id(employee_id)
        if user is None or user.role != UserRole.EXECUTIVE:
            return PasswordResetStatusOut(
                employee_id=employee_id,
                approved=False,
                message="No executive account found for this employee ID",
            )

        # Prefer an unused approval even if a newer pending somehow exists.
        open_approved = await self.reset_repo.get_open_approved_for_user(user.id)
        if open_approved is not None:
            return PasswordResetStatusOut(
                employee_id=employee_id,
                status=PasswordResetStatus.APPROVED,
                approved=True,
                message="Reset approved. Set your new password now.",
            )

        latest = await self.reset_repo.get_latest_for_user(user.id)
        if latest is None:
            return PasswordResetStatusOut(
                employee_id=employee_id,
                approved=False,
                message="No password reset request found",
            )

        if latest.status == PasswordResetStatus.PENDING:
            return PasswordResetStatusOut(
                employee_id=employee_id,
                status=PasswordResetStatus.PENDING,
                approved=False,
                message="Reset request is pending admin approval",
            )

        if latest.status == PasswordResetStatus.COMPLETED or (
            latest.status == PasswordResetStatus.APPROVED
            and latest.temp_password_hash == "__used__"
        ):
            return PasswordResetStatusOut(
                employee_id=employee_id,
                status=PasswordResetStatus.COMPLETED,
                approved=False,
                message="Password was already updated for this reset request",
            )

        return PasswordResetStatusOut(
            employee_id=employee_id,
            status=latest.status,
            approved=False,
            message="Password reset request was rejected",
        )

    async def approve(self, request_id: uuid.UUID) -> PasswordResetRequest:
        """Admin approval only — does not change the user's password."""
        request = await self.reset_repo.get_by_id(request_id)
        if request is None:
            raise PasswordResetError("Password reset request not found")
        if request.status != PasswordResetStatus.PENDING:
            raise PasswordResetError("Password reset request is no longer pending")

        return await self.reset_repo.resolve(
            request,
            status=PasswordResetStatus.APPROVED,
            temp_password_hash=None,
        )

    async def set_password_after_approval(
        self, *, employee_id: str, new_password: str
    ) -> PasswordResetRequest:
        """Set a new password after admin approval (no login / current password)."""
        user = await self.user_repo.get_by_employee_id(employee_id)
        if user is None or user.role != UserRole.EXECUTIVE:
            raise PasswordResetError("No executive account found for this employee ID")
        if user.is_blocked:
            raise PasswordResetError("This account has been blocked. Contact your admin.")

        latest = await self.reset_repo.get_open_approved_for_user(user.id)
        if latest is None:
            raise PasswordResetError(
                "No approved password reset found. Request a reset and wait for admin approval."
            )

        if len(new_password) < 6:
            raise PasswordResetError("Password must be at least 6 characters")

        user.password_hash = hash_password(new_password)
        await self.user_repo.update(user)

        open_approvals = await self.reset_repo.list_open_approved_for_user(user.id)
        consumed = open_approvals[0]
        for approval in open_approvals:
            await self.reset_repo.resolve(
                approval,
                status=PasswordResetStatus.APPROVED,
                temp_password_hash="__used__",
            )
        return consumed

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
