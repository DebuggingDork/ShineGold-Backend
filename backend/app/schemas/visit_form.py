import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import FormQuestionType


class FormQuestionOptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    value: str
    label: str
    sort_order: int


class FormQuestionOptionCreate(BaseModel):
    value: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=255)
    sort_order: int = 0


class FormQuestionOptionUpdate(BaseModel):
    value: str | None = Field(default=None, min_length=1, max_length=100)
    label: str | None = Field(default=None, min_length=1, max_length=255)
    sort_order: int | None = None


class FormQuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_key: str
    label: str
    help_text: str | None = None
    question_type: FormQuestionType
    sort_order: int
    is_required: bool
    config: dict | None = None
    options: list[FormQuestionOptionOut] = []


class FormQuestionCreate(BaseModel):
    question_key: str = Field(min_length=1, max_length=100)
    label: str = Field(min_length=1, max_length=500)
    help_text: str | None = None
    question_type: FormQuestionType
    sort_order: int = 0
    is_required: bool = True
    config: dict | None = None
    options: list[FormQuestionOptionCreate] = Field(default_factory=list)


class FormQuestionUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=500)
    help_text: str | None = None
    question_type: FormQuestionType | None = None
    sort_order: int | None = None
    is_required: bool | None = None
    config: dict | None = None


class FormTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None = None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
    questions: list[FormQuestionOut] = []


class FormTemplateSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None = None
    is_active: bool
    is_default: bool
    question_count: int = 0


class FormTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    activate: bool = False


class FormTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None


class FormAnswerIn(BaseModel):
    question_key: str
    answer: str | None = None
    answer_json: dict | list | None = None


class FormAnswerOut(BaseModel):
    question_key: str
    question_label: str
    question_type: FormQuestionType
    answer: str | None = None
    answer_json: dict | list | None = None


class VisitFormPrefillOut(BaseModel):
    executive_name: str
    visit_date: str
    farm_location: str | None = None
    farmer_contact_name: str | None = None
    checkin_time: datetime | None = None


class VisitFormContextOut(BaseModel):
    template: FormTemplateOut
    prefill: VisitFormPrefillOut
