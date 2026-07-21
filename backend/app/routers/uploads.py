from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.upload import PresignRequest, PresignResponse
from app.services.storage_service import StorageError, storage_service

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])


class ResolveMediaRequest(BaseModel):
    url: str = Field(min_length=1)


class ResolveMediaResponse(BaseModel):
    url: str
    object_key: str | None = None
    signed: bool = False


@router.post("/presign", response_model=PresignResponse)
async def presign_upload(
    payload: PresignRequest,
    _current_user: User = Depends(get_current_user),
):
    try:
        result = storage_service.generate_presigned_upload(payload.file_type, payload.context)
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return PresignResponse(**result)


@router.post("/resolve", response_model=ResolveMediaResponse)
async def resolve_media_url(
    payload: ResolveMediaRequest,
    _current_user: User = Depends(get_current_user),
):
    """Return a playable URL for stored media (fresh signed URL when possible)."""
    raw = payload.url.strip()
    if not raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="url is required")

    object_key = storage_service.object_key_from_public_url(raw)
    if object_key is None:
        # Already an absolute non-Supabase URL — pass through
        if raw.startswith("http://") or raw.startswith("https://"):
            return ResolveMediaResponse(url=raw, signed=False)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unrecognized media URL",
        )

    try:
        signed_url = storage_service.create_signed_download_url(object_key)
    except StorageError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e

    return ResolveMediaResponse(url=signed_url, object_key=object_key, signed=True)
