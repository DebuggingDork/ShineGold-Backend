import uuid
from datetime import datetime, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import PasswordResetStatus
from app.models.user import PasswordResetRequest


class PasswordResetRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, request_id: uuid.UUID) -> PasswordResetRequest | None:
        result = await self.db.execute(
            select(PasswordResetRequest)
            .where(PasswordResetRequest.id == request_id)
            .options(selectinload(PasswordResetRequest.user))
        )
        return result.scalar_one_or_none()

    async def get_pending_for_user(self, user_id: uuid.UUID) -> PasswordResetRequest | None:
        result = await self.db.execute(
            select(PasswordResetRequest).where(
                PasswordResetRequest.user_id == user_id,
                PasswordResetRequest.status == PasswordResetStatus.PENDING,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, user_id: uuid.UUID) -> PasswordResetRequest:
        request = PasswordResetRequest(user_id=user_id)
        self.db.add(request)
        await self.db.flush()
        await self.db.refresh(request)
        return request

    async def list_requests(
        self,
        *,
        status: PasswordResetStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PasswordResetRequest], int]:
        filters = []
        if status is not None:
            filters.append(PasswordResetRequest.status == status)

        base_query = (
            select(PasswordResetRequest)
            .options(selectinload(PasswordResetRequest.user))
            .order_by(PasswordResetRequest.requested_at.desc())
        )
        count_query = select(func.count()).select_from(PasswordResetRequest)

        if filters:
            base_query = base_query.where(and_(*filters))
            count_query = count_query.where(and_(*filters))

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        result = await self.db.execute(
            base_query.offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().unique().all()), total

    async def resolve(
        self,
        request: PasswordResetRequest,
        *,
        status: PasswordResetStatus,
        temp_password_hash: str | None = None,
    ) -> PasswordResetRequest:
        request.status = status
        request.temp_password_hash = temp_password_hash
        request.resolved_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(request)
        return request
