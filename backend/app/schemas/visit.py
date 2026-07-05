import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

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


class VisitPhotoIn(BaseModel):
    photo_url: str
    captured_lat: float
    captured_lng: float
    captured_at: datetime


class VisitPhotoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    photo_url: str
    captured_lat: float
    captured_lng: float
    captured_at: datetime


class VisitFormUpdate(BaseModel):
    photos: list[VisitPhotoIn] | None = None
    voice_note_url: str | None = None
    text_note: str | None = None
    mcq_answers: list[McqAnswerIn] | None = None


class VisitFormResponse(BaseModel):
    visit_id: uuid.UUID
    status: VisitStatus
    updated_fields: list[str]


class VisitSubmitRequest(BaseModel):
    checkout_lat: float
    checkout_lng: float


class VisitSubmitResponse(BaseModel):
    visit_id: uuid.UUID
    status: VisitStatus
    checkout_time: datetime
    duration_seconds: int


class VisitFarmSummary(BaseModel):
    id: uuid.UUID
    name: str


class VisitMineItem(BaseModel):
    visit_id: uuid.UUID
    farm: VisitFarmSummary
    status: VisitStatus
    checkin_time: datetime
    duration_seconds: int | None = None


class McqAnswerOut(BaseModel):
    question_key: str
    answer: str


class VisitExecutiveSummary(BaseModel):
    id: uuid.UUID
    name: str


class VisitDetailOut(BaseModel):
    visit_id: uuid.UUID
    farm_id: uuid.UUID
    status: VisitStatus
    checkin_time: datetime
    checkout_time: datetime | None = None
    duration_seconds: int | None = None
    text_note: str | None = None
    photos: list[str] = []
    voice_note_url: str | None = None
    mcq_answers: list[McqAnswerOut] = []
    visited_by: VisitExecutiveSummary