from fastapi import APIRouter, Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.upload import PresignRequest, PresignResponse
from app.services.storage_service import StorageError, storage_service

router = APIRouter(prefix="/api/v1/uploads", tags=["uploads"])


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
