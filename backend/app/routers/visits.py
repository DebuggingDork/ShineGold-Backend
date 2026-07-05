from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_executive
from app.models.user import User
from app.repositories.farm_repository import FarmRepository
from app.repositories.visit_repository import VisitRepository
from app.schemas.visit import CheckinRequest, CheckinResponse

router = APIRouter(prefix="/api/v1/visits", tags=["visits"])


@router.post("/checkin", response_model=CheckinResponse, status_code=status.HTTP_201_CREATED)
async def checkin(
    payload: CheckinRequest,
    current_user: User = Depends(require_executive),
    db: AsyncSession = Depends(get_db),
):
    farm_repo = FarmRepository(db)
    farm = await farm_repo.get_by_id(payload.farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    visit_repo = VisitRepository(db)
    existing = await visit_repo.get_in_progress_for_executive(current_user.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a visit in progress. Submit or cancel it first.",
        )

    visit = await visit_repo.create_checkin(
        farm_id=payload.farm_id,
        executive_id=current_user.id,
        checkin_lat=payload.checkin_lat,
        checkin_lng=payload.checkin_lng,
    )
    await db.commit()

    return CheckinResponse(
        visit_id=visit.id,
        farm_id=visit.farm_id,
        status=visit.status,
        checkin_time=visit.checkin_time,
    )
