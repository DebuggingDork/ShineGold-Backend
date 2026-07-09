from datetime import date
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_executive
from app.models.enums import UserRole, VisitStatus
from app.models.user import User
from app.models.visit import Visit
from app.repositories.farm_repository import FarmRepository
from app.repositories.visit_repository import VisitRepository
from app.services.farm_assignment_service import FarmAssignmentService
from app.schemas.common import PaginatedResponse
from app.schemas.visit import (
    CheckinRequest,
    CheckinResponse,
    VisitDetailOut,
    VisitFormResponse,
    VisitFormUpdate,
    VisitMineItem,
    VisitSubmitRequest,
    VisitSubmitResponse,
)

router = APIRouter(prefix="/api/v1/visits", tags=["visits"])


def _require_in_progress_visit(visit: Visit | None, executive_id: uuid.UUID) -> Visit:
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")
    if visit.executive_id != executive_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this visit",
        )
    if visit.status != VisitStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Visit is not in progress",
        )
    return visit


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

    if not FarmAssignmentService.can_visit_farm(current_user, farm):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this farm. Onboard it or accept a nearby invitation first.",
        )

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


@router.get("/mine", response_model=PaginatedResponse[VisitMineItem])
async def list_my_visits(
    status: VisitStatus | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    farm_name: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_executive),
    db: AsyncSession = Depends(get_db),
):
    visit_repo = VisitRepository(db)
    visits, total = await visit_repo.list_mine(
        current_user.id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        farm_name=farm_name,
        page=page,
        page_size=page_size,
    )
    items = [VisitRepository.to_mine_item(visit) for visit in visits]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{visit_id}", response_model=VisitDetailOut)
async def get_visit(
    visit_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    visit_repo = VisitRepository(db)
    visit = await visit_repo.get_by_id(visit_id)
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visit not found")

    if current_user.role != UserRole.SUPER_ADMIN and visit.executive_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this visit",
        )

    return VisitRepository.to_detail(visit)


@router.patch("/{visit_id}/form", response_model=VisitFormResponse)
async def update_visit_form(
    visit_id: uuid.UUID,
    payload: VisitFormUpdate,
    current_user: User = Depends(require_executive),
    db: AsyncSession = Depends(get_db),
):
    visit_repo = VisitRepository(db)
    visit = _require_in_progress_visit(
        await visit_repo.get_by_id(visit_id), current_user.id
    )

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    updated_fields = await visit_repo.update_form(visit, payload)
    await db.commit()

    return VisitFormResponse(
        visit_id=visit.id,
        status=visit.status,
        updated_fields=updated_fields,
    )


@router.post("/{visit_id}/submit", response_model=VisitSubmitResponse)
async def submit_visit(
    visit_id: uuid.UUID,
    payload: VisitSubmitRequest,
    current_user: User = Depends(require_executive),
    db: AsyncSession = Depends(get_db),
):
    visit_repo = VisitRepository(db)
    visit = _require_in_progress_visit(
        await visit_repo.get_by_id(visit_id), current_user.id
    )

    visit = await visit_repo.submit(
        visit,
        checkout_lat=payload.checkout_lat,
        checkout_lng=payload.checkout_lng,
    )
    await db.commit()

    return VisitSubmitResponse(
        visit_id=visit.id,
        status=visit.status,
        checkout_time=visit.checkout_time,
        duration_seconds=visit.duration_seconds,
    )
