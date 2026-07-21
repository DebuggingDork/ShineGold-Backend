import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, AliasChoices

from app.models.enums import VisitStatus
from app.schemas.visit_form import FormAnswerIn, FormAnswerOut


class CheckinRequest(BaseModel):
    farm_id: uuid.UUID
    checkin_lat: float = Field(validation_alias=AliasChoices("checkin_lat", "latitude"))
    checkin_lng: float = Field(validation_alias=AliasChoices("checkin_lng", "longitude"))

    model_config = ConfigDict(populate_by_name=True)


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
    # Client-reported length; rejected when above Settings.MAX_VOICE_NOTE_SECONDS
    voice_note_duration_seconds: int | None = Field(default=None, ge=0)
    text_note: str | None = None
    mcq_answers: list[McqAnswerIn] | None = None
    form_answers: list[FormAnswerIn] | None = None


class VisitFormResponse(BaseModel):
    visit_id: uuid.UUID
    status: VisitStatus
    updated_fields: list[str]


class VisitSubmitRequest(BaseModel):
    checkout_lat: float = Field(validation_alias=AliasChoices("checkout_lat", "latitude"))
    checkout_lng: float = Field(validation_alias=AliasChoices("checkout_lng", "longitude"))

    model_config = ConfigDict(populate_by_name=True)


class VisitSubmitResponse(BaseModel):
    visit_id: uuid.UUID
    status: VisitStatus
    checkout_time: datetime
    duration_seconds: int


class VisitCancelResponse(BaseModel):
    visit_id: uuid.UUID
    status: VisitStatus


class VisitFarmSummary(BaseModel):
    id: uuid.UUID
    name: str


class VisitExecutiveSummary(BaseModel):
    id: uuid.UUID
    name: str


class VisitMineItem(BaseModel):
    visit_id: uuid.UUID
    farm: VisitFarmSummary
    status: VisitStatus
    checkin_time: datetime
    checkout_time: datetime | None = None
    duration_seconds: int | None = None
    remarks_preview: str | None = None
    has_voice_note: bool = False
    photo_count: int = 0


class VisitHistoryItem(BaseModel):
    visit_id: uuid.UUID
    farm_id: uuid.UUID
    farm_name: str
    status: VisitStatus
    checkin_time: datetime
    checkout_time: datetime | None = None
    duration_seconds: int | None = None
    remarks_preview: str | None = None
    has_voice_note: bool = False
    photo_count: int = 0
    visited_by: VisitExecutiveSummary


class McqAnswerOut(BaseModel):
    question_key: str
    answer: str


class VisitDetailOut(BaseModel):
    visit_id: uuid.UUID
    farm_id: uuid.UUID
    farm_name: str
    status: VisitStatus
    checkin_time: datetime
    checkout_time: datetime | None = None
    duration_seconds: int | None = None
    text_note: str | None = None
    photos: list[VisitPhotoOut] = []
    voice_note_url: str | None = None
    mcq_answers: list[McqAnswerOut] = []
    form_answers: list[FormAnswerOut] = []
    visited_by: VisitExecutiveSummary
    has_voice_note: bool = False
    has_photos: bool = False