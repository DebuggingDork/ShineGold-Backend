import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import VisitStatus


class CheckinRequest(BaseModel):
    farm_id: uuid.UUID
    checkin_lat: float
    checkin_lng: float


class CheckinResponse(BaseModel):
    visit_id: uuid.UUID
    farm_id: uuid.UUID
    status: VisitStatus
    checkin_time: datetime


class McqAnswerIn(BaseModel):
    question_key: str
    answer: str


class VisitFormUpdate(BaseModel):
    photos: list[str] | None = None
    voice_note_url: str | None = None
    text_note: str | None = None
    mcq_answers: list[McqAnswerIn] | None = None


class VisitSubmitRequest(BaseModel):
    checkout_lat: float
    checkout_lng: float


class VisitSubmitResponse(BaseModel):
    visit_id: uuid.UUID
    status: VisitStatus
    checkout_time: datetime
    duration_seconds: int