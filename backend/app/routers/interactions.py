import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_executive
from app.models.enums import InteractionStatus
from app.models.user import User
from app.repositories.interaction_repository import InteractionRepository
from app.schemas.common import PaginatedResponse
from app.schemas.interaction import InteractionCreate, InteractionOut, InteractionUpdate

router = APIRouter(prefix="/api/v1/interactions", tags=["interactions"])


@router.post("", response_model=InteractionOut, status_code=status.HTTP_201_CREATED)
async def create_interaction(
    body: InteractionCreate,
    current_user: User = Depends(require_executive),
    db: AsyncSession = Depends(get_db),
):
    repo = InteractionRepository(db)
    return await repo.create(executive_id=current_user.id, data=body)


@router.get("/mine", response_model=PaginatedResponse[InteractionOut])
async def list_my_interactions(
    search: str | None = Query(None),
    status_filter: InteractionStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    current_user: User = Depends(require_executive),
    db: AsyncSession = Depends(get_db),
):
    repo = InteractionRepository(db)
    items, total = await repo.list_for_executive(
        executive_id=current_user.id,
        search=search,
        status=status_filter,
        page=page,
        page_size=page_size,
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{interaction_id}", response_model=InteractionOut)
async def get_interaction(
    interaction_id: uuid.UUID,
    current_user: User = Depends(require_executive),
    db: AsyncSession = Depends(get_db),
):
    repo = InteractionRepository(db)
    row = await repo.get_by_id(interaction_id)
    if row is None or row.executive_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found",
        )
    return row


@router.patch("/{interaction_id}", response_model=InteractionOut)
async def update_interaction(
    interaction_id: uuid.UUID,
    body: InteractionUpdate,
    current_user: User = Depends(require_executive),
    db: AsyncSession = Depends(get_db),
):
    repo = InteractionRepository(db)
    row = await repo.get_by_id(interaction_id)
    if row is None or row.executive_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interaction not found",
        )
    return await repo.update(row, body)
