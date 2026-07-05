from typing import Literal

from pydantic import BaseModel

UploadContext = Literal[
    "farm_photo",
    "farmer_photo",
    "profile_photo",
    "visit_photo",
    "visit_voice",
]


class PresignRequest(BaseModel):
    file_type: str
    context: UploadContext


class PresignResponse(BaseModel):
    upload_url: str
    object_key: str
    public_url: str
    expires_in: int
