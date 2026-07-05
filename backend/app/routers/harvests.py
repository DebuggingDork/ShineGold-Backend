from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_super_admin
from app.models.user import User
from app.repositories.harvest_repository import HarvestRepository
from app.schemas.harvest import HarvestCalendarOut

router = APIRouter(prefix="/api/v1/harvests", tags=["harvests"])


@router.get("/calendar", response_model=HarvestCalendarOut)
async def get_harvest_calendar(
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    harvest_repo = HarvestRepository(db)
    try:
        return await harvest_repo.get_calendar(
            month=month,
            date_from=date_from,
            date_to=date_to,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
