import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_super_admin
from app.models.user import User
from app.repositories.farmer_repository import FarmerRepository
from app.schemas.common import PaginatedResponse
from app.schemas.farmer import FarmerDetailOut, FarmerListItem

router = APIRouter(prefix="/api/v1/farmers", tags=["farmers"])


@router.get("", response_model=PaginatedResponse[FarmerListItem])
async def list_farmers(
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    farmer_repo = FarmerRepository(db)
    farmers, total = await farmer_repo.list_farmers(
        search=search,
        page=page,
        page_size=page_size,
    )
    items = [FarmerRepository.to_list_item(farmer) for farmer in farmers]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{farmer_id}", response_model=FarmerDetailOut)
async def get_farmer(
    farmer_id: uuid.UUID,
    _current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    farmer_repo = FarmerRepository(db)
    farmer = await farmer_repo.get_by_id(farmer_id)
    if farmer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found")

    return FarmerRepository.to_detail(farmer)
