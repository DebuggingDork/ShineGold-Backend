import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_executive
from app.models.enums import FarmStatus
from app.models.user import User
from app.repositories.farm_repository import FarmRepository
from app.schemas.common import PaginatedResponse
from app.schemas.farm import FarmCreate, FarmCreateOut, FarmListItem

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
