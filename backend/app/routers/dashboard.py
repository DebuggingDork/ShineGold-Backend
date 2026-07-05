from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_super_admin
from app.models.user import User
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard import AdminDashboardOut

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])


@router.get("/admin", response_model=AdminDashboardOut)
async def get_admin_dashboard(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    dashboard_repo = DashboardRepository(db)
    return await dashboard_repo.get_admin_stats(
        date_from=date_from,
        date_to=date_to,
    )
