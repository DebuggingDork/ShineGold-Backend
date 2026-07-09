import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user, get_db, require_executive, require_super_admin
from app.core.http import raise_bad_request, raise_not_found
from app.core.config import settings
from app.models.enums import FarmStatus, UserRole
from app.models.user import User
from app.repositories.farm_repository import FarmRepository
from app.repositories.visit_repository import VisitRepository
from app.schemas.common import PaginatedResponse
from app.schemas.farm import (
    FarmAcceptOut,
    FarmAdminCreate,
    FarmAssignOut,
    FarmAssignUpdate,
    FarmCreate,
    FarmCreateOut,
    FarmDetailOut,
    FarmInvitationItem,
    FarmListItem,
    FarmUpdate,
)
from app.schemas.visit import VisitDetailOut, VisitHistoryItem
from app.services.farm_assignment_service import FarmAssignmentError, FarmAssignmentService
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
        assigned_executive_ids=FarmRepository.assigned_executive_ids(farm),
        created_at=farm.created_at,
    )


@router.post("/admin", response_model=FarmCreateOut, status_code=status.HTTP_201_CREATED)
async def create_farm_as_admin(
    payload: FarmAdminCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Super admin creates a farm directly and optionally assigns one or more executives."""
    user_service = UserService(db)
    for executive_id in payload.executive_ids:
        try:
            await user_service.get_assignable_executive(executive_id)
        except UserServiceError as e:
            raise_bad_request(str(e))

    farm_repo = FarmRepository(db)
    farm, farmer = await farm_repo.create(
        payload,
        onboarded_by=current_user.id,
        executive_ids=payload.executive_ids,
        assigned_by=current_user.id,
    )
    await db.commit()

    return FarmCreateOut(
        id=farm.id,
        name=farm.name,
        status=farm.status,
        farmer_id=farmer.id,
        assigned_executive_ids=FarmRepository.assigned_executive_ids(farm),
        created_at=farm.created_at,
    )


@router.get("/invitations", response_model=PaginatedResponse[FarmInvitationItem])
async def list_farm_invitations(
    lat: float | None = Query(None, description="Device latitude for distance display"),
    lng: float | None = Query(None, description="Device longitude for distance display"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_executive),
    db: AsyncSession = Depends(get_db),
):
    """Unassigned farms within home-location coverage; optional lat/lng for display distance."""
    assignment_service = FarmAssignmentService(db)
    try:
        rows, total = await assignment_service.list_invitations(
            current_user,
            display_lat=lat,
            display_lng=lng,
            page=page,
            page_size=page_size,
        )
    except FarmAssignmentError as e:
        raise_bad_request(str(e))

    items = []
    for farm, distance_km in rows:
        list_item = FarmRepository.to_list_item(farm, distance_km, None)
        items.append(
            FarmInvitationItem(
                id=farm.id,
                name=farm.name,
                location_address=farm.location_address,
                location_lat=farm.location_lat,
                location_lng=farm.location_lng,
                location=list_item["location"],
                distance_km=distance_km,
                farmer=list_item["farmer"],
                status=farm.status,
                assignment_radius_km=settings.EXECUTIVE_ASSIGNMENT_RADIUS_KM,
            )
        )
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size)


@router.post("/{farm_id}/accept", response_model=FarmAcceptOut)
async def accept_farm_invitation(
    farm_id: uuid.UUID,
    current_user: User = Depends(require_executive),
    db: AsyncSession = Depends(get_db),
):
    """Accept proximity-based assignment for an unassigned farm within coverage radius."""
    assignment_service = FarmAssignmentService(db)
    try:
        farm = await assignment_service.accept_invitation(current_user, farm_id)
        distance_km = round(assignment_service.distance_to_farm(current_user, farm), 1)
    except FarmAssignmentError as e:
        raise_bad_request(str(e))

    await db.commit()
    return FarmAcceptOut(
        farm_id=farm.id,
        assigned_executive_ids=FarmRepository.assigned_executive_ids(farm),
        distance_km=distance_km,
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
    current_user: User = Depends(get_current_user),
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
    elif current_user.role == UserRole.EXECUTIVE:
        assigned_to_id = current_user.id

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
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    farm_repo = FarmRepository(db)
    farm = await farm_repo.get_by_id(farm_id)
    if farm is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farm not found")

    if current_user.role == UserRole.EXECUTIVE and not FarmRepository.is_executive_assigned(
        farm, current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this farm",
        )

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

    await farm_repo.update(farm, **update_data)
    await db.commit()

    updated_farm = await farm_repo.get_by_id(farm_id)
    return FarmRepository.to_detail(updated_farm)


@router.patch("/{farm_id}/assign", response_model=FarmAssignOut)
async def assign_farm_executives(
    farm_id: uuid.UUID,
    payload: FarmAssignUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Assign one or more executives to a farm. Use mode=replace|add|remove."""
    farm_repo = FarmRepository(db)
    farm = await farm_repo.get_by_id(farm_id)
    if farm is None:
        raise_not_found("Farm not found")

    user_service = UserService(db)
    for executive_id in payload.executive_ids:
        try:
            await user_service.get_assignable_executive(executive_id)
        except UserServiceError as e:
            raise_bad_request(str(e))

    assignment_service = FarmAssignmentService(db)
    try:
        farm = await assignment_service.assign_executives(
            farm,
            payload.executive_ids,
            assigned_by=current_user.id,
            mode=payload.mode,
        )
    except FarmAssignmentError as e:
        raise_bad_request(str(e))

    await db.commit()
    return FarmAssignOut(
        farm_id=farm.id,
        assigned_executive_ids=FarmRepository.assigned_executive_ids(farm),
    )
