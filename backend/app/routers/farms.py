import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_executive, require_super_admin
from app.core.http import raise_bad_request, raise_not_found
from app.models.enums import FarmStatus
from app.models.user import User
from app.repositories.farm_repository import FarmRepository
from app.repositories.visit_repository import VisitRepository
from app.schemas.common import PaginatedResponse
from app.schemas.farm import (
    FarmAssignOut,
    FarmAssignUpdate,
    FarmCreate,
    FarmCreateOut,
    FarmDetailOut,
    FarmListItem,
    FarmUpdate,
)
from app.schemas.visit import VisitDetailOut, VisitHistoryItem
from app.services.user_service import UserService, UserServiceError

router = APIRouter(prefix="/api/v1/farms", tags=["farms"])


@router.post("", response_model=FarmCreateOut, status_code=status.HTTP_201_CREATED)
async def onboard_farm(
    payload: FarmCreate,
    current_user: User = Depends(require_executive),
    db: AsyncSession = Depends(get_db),
):
    farm_repo = FarmRepository(db)
    farm, farmer = await farm_repo.create(payload, onboarded_by=current_user.id)
    await db.commit()

    return FarmCreateOut(
        id=farm.id,
        name=farm.name,
        status=farm.status,
        farmer_id=farmer.id,
        created_at=farm.created_at,
    )


@router.get("", response_model=PaginatedResponse[FarmListItem])
async def list_farms(
    lat: float | None = Query(None),
    lng: float | None = Query(None),
    sort: Literal["distance", "farthest"] | None = Query(None),
    harvest_status: FarmStatus | None = Query(None),
    assigned_to: str | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    assigned_to_id = None
    if assigned_to is not None:
        try:
            assigned_to_id = uuid.UUID(assigned_to)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="assigned_to must be a valid UUID",
            ) from e

    farm_repo = FarmRepository(db)
    try:
        rows, total = await farm_repo.list_farms(
            lat=lat,
            lng=lng,
            sort=sort,
            harvest_status=harvest_status,
            assigned_to=assigned_to_id,
            search=search,
            page=page,
            page_size=page_size,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    items = [FarmListItem(**FarmRepository.to_list_item(farm, distance, last_visited)) for farm, distance, last_visited in rows]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{farm_id}/visits/latest", response_model=VisitDetailOut)
async def get_farm_latest_visit(
    farm_id: uuid.UUID,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    farm_repo = FarmRepository(db)
    farm = await farm_repo.get_by_id(farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    visit_repo = VisitRepository(db)
    visit = await visit_repo.get_latest_completed_for_farm(farm_id)
    if visit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No completed visits for this farm")

    return VisitRepository.to_detail(visit)


@router.get("/{farm_id}/visits", response_model=PaginatedResponse[VisitHistoryItem])
async def list_farm_visits(
    farm_id: uuid.UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    farm_repo = FarmRepository(db)
    farm = await farm_repo.get_by_id(farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    visit_repo = VisitRepository(db)
    visits, total = await visit_repo.list_for_farm(farm_id, page=page, page_size=page_size)
    items = [VisitRepository.to_history_item(visit) for visit in visits]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{farm_id}", response_model=FarmDetailOut)
async def get_farm(
    farm_id: uuid.UUID,
    _current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    farm_repo = FarmRepository(db)
    farm = await farm_repo.get_by_id(farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    return FarmRepository.to_detail(farm)


@router.patch("/{farm_id}", response_model=FarmDetailOut)
async def update_farm(
    farm_id: uuid.UUID,
    payload: FarmUpdate,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    farm_repo = FarmRepository(db)
    farm = await farm_repo.get_by_id(farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No fields to update")

    if "assigned_executive_id" in update_data:
        user_service = UserService(db)
        try:
            await user_service.get_assignable_executive(update_data["assigned_executive_id"])
        except UserServiceError as e:
            raise_bad_request(str(e))

    await farm_repo.update(farm, **update_data)
    await db.commit()

    updated_farm = await farm_repo.get_by_id(farm_id)
    return FarmRepository.to_detail(updated_farm)


@router.patch("/{farm_id}/assign", response_model=FarmAssignOut)
async def assign_farm_executive(
    farm_id: uuid.UUID,
    payload: FarmAssignUpdate,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    farm_repo = FarmRepository(db)
    farm = await farm_repo.get_by_id(farm_id)
    if farm is None:
        raise_not_found("Farm not found")

    user_service = UserService(db)
    try:
        await user_service.get_assignable_executive(payload.executive_id)
    except UserServiceError as e:
        raise_bad_request(str(e))

    await farm_repo.update(farm, assigned_executive_id=payload.executive_id)
    await db.commit()

    return FarmAssignOut(farm_id=farm.id, assigned_executive_id=payload.executive_id)
