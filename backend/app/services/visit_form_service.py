import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import FormQuestionType
from app.models.farm import Farm
from app.models.user import User
from app.models.visit import Visit
from app.models.visit_form import VisitFormAnswer, VisitFormQuestion, VisitFormTemplate
from app.repositories.visit_form_repository import VisitFormRepository
from app.schemas.visit_form import (
    FormAnswerIn,
    FormAnswerOut,
    FormQuestionCreate,
    FormQuestionOptionCreate,
    FormQuestionOptionUpdate,
    FormQuestionOut,
    FormQuestionUpdate,
    FormTemplateCreate,
    FormTemplateOut,
    FormTemplateSummary,
    FormTemplateUpdate,
    VisitFormContextOut,
    VisitFormPrefillOut,
)


class VisitFormServiceError(Exception):
    pass


class VisitFormService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = VisitFormRepository(db)

    async def get_active_template(self) -> FormTemplateOut:
        template = await self.repo.get_active_template()
        if template is None:
            raise VisitFormServiceError("No active visit form template configured")
        return self._to_template_out(template)

    async def list_templates(self) -> list[FormTemplateSummary]:
        templates = await self.repo.list_templates()
        summaries: list[FormTemplateSummary] = []
        for template in templates:
            count = await self.repo.count_questions(template.id)
            summaries.append(
                FormTemplateSummary(
                    id=template.id,
                    name=template.name,
                    description=template.description,
                    is_active=template.is_active,
                    is_default=template.is_default,
                    question_count=count,
                )
            )
        return summaries

    async def get_template(self, template_id: uuid.UUID) -> FormTemplateOut:
        template = await self.repo.get_template_by_id(template_id)
        if template is None:
            raise VisitFormServiceError("Form template not found")
        return self._to_template_out(template)

    async def create_template(self, payload: FormTemplateCreate) -> FormTemplateOut:
        template = await self.repo.create_template(payload)
        loaded = await self.repo.get_template_by_id(template.id)
        return self._to_template_out(loaded)

    async def update_template(
        self, template_id: uuid.UUID, payload: FormTemplateUpdate
    ) -> FormTemplateOut:
        template = await self.repo.get_template_by_id(template_id)
        if template is None:
            raise VisitFormServiceError("Form template not found")
        if template.is_default and payload.name is not None:
            raise VisitFormServiceError("Cannot rename the default system template")
        await self.repo.update_template(template, payload)
        loaded = await self.repo.get_template_by_id(template_id)
        return self._to_template_out(loaded)

    async def activate_template(self, template_id: uuid.UUID) -> FormTemplateOut:
        template = await self.repo.get_template_by_id(template_id)
        if template is None:
            raise VisitFormServiceError("Form template not found")
        await self.repo.activate_template(template)
        loaded = await self.repo.get_template_by_id(template_id)
        return self._to_template_out(loaded)

    async def add_question(
        self, template_id: uuid.UUID, payload: FormQuestionCreate
    ) -> FormQuestionOut:
        template = await self.repo.get_template_by_id(template_id)
        if template is None:
            raise VisitFormServiceError("Form template not found")
        self._validate_question_payload(payload.question_type, payload.options, payload.config)
        question = await self.repo.create_question(template, payload)
        return FormQuestionOut.model_validate(question)

    async def update_question(
        self, question_id: uuid.UUID, payload: FormQuestionUpdate
    ) -> FormQuestionOut:
        question = await self.repo.get_question_by_id(question_id)
        if question is None:
            raise VisitFormServiceError("Form question not found")
        await self.repo.update_question(question, payload)
        refreshed = await self.repo.get_question_by_id(question_id)
        return FormQuestionOut.model_validate(refreshed)

    async def delete_question(self, question_id: uuid.UUID) -> None:
        question = await self.repo.get_question_by_id(question_id)
        if question is None:
            raise VisitFormServiceError("Form question not found")
        await self.repo.delete_question(question)

    async def add_option(
        self, question_id: uuid.UUID, payload: FormQuestionOptionCreate
    ) -> FormQuestionOut:
        question = await self.repo.get_question_by_id(question_id)
        if question is None:
            raise VisitFormServiceError("Form question not found")
        if question.question_type not in (
            FormQuestionType.SINGLE_CHOICE,
            FormQuestionType.MULTI_CHOICE,
        ):
            raise VisitFormServiceError("Options can only be added to choice questions")
        await self.repo.create_option(question, payload)
        refreshed = await self.repo.get_question_by_id(question_id)
        return FormQuestionOut.model_validate(refreshed)

    async def update_option(
        self, option_id: uuid.UUID, payload: FormQuestionOptionUpdate
    ) -> FormQuestionOut:
        option = await self.repo.get_option_by_id(option_id)
        if option is None:
            raise VisitFormServiceError("Form option not found")
        await self.repo.update_option(option, payload)
        refreshed = await self.repo.get_question_by_id(option.question_id)
        return FormQuestionOut.model_validate(refreshed)

    async def delete_option(self, option_id: uuid.UUID) -> None:
        option = await self.repo.get_option_by_id(option_id)
        if option is None:
            raise VisitFormServiceError("Form option not found")
        await self.repo.delete_option(option)

    async def build_visit_context(self, visit: Visit) -> VisitFormContextOut:
        template = await self.repo.get_active_template()
        if template is None:
            raise VisitFormServiceError("No active visit form template configured")

        farm: Farm = visit.farm
        executive: User = visit.executive
        farmer_name = farm.farmer.name if farm.farmer else None

        return VisitFormContextOut(
            template=self._to_template_out(template),
            prefill=VisitFormPrefillOut(
                executive_name=executive.name,
                visit_date=visit.checkin_time.date().isoformat(),
                farm_location=farm.location_address,
                farmer_contact_name=farmer_name,
                checkin_time=visit.checkin_time,
            ),
        )

    async def save_visit_answers(
        self, visit: Visit, answers: list[FormAnswerIn]
    ) -> list[str]:
        template = await self.repo.get_active_template()
        if template is None:
            raise VisitFormServiceError("No active visit form template configured")

        questions_by_key = {
            q.question_key: q
            for q in template.questions
            if q.question_type != FormQuestionType.SECTION_HEADER
        }

        stored: list[VisitFormAnswer] = []
        for item in answers:
            question = questions_by_key.get(item.question_key)
            if question is None:
                raise VisitFormServiceError(f"Unknown question key: {item.question_key}")
            answer_text, answer_json = self._normalize_answer(question, item)
            stored.append(
                VisitFormAnswer(
                    visit_id=visit.id,
                    question_key=question.question_key,
                    question_label=question.label,
                    question_type=question.question_type,
                    answer_text=answer_text,
                    answer_json=answer_json,
                )
            )

        await self.repo.upsert_visit_answers(visit.id, stored)
        return ["form_answers"]

    async def validate_required_answers(self, visit_id: uuid.UUID) -> None:
        template = await self.repo.get_active_template()
        if template is None:
            return

        answers = await self.repo.get_visit_answers(visit_id)
        answered_keys = {answer.question_key for answer in answers if self._has_value(answer)}

        missing = [
            question.label
            for question in template.questions
            if question.is_required
            and question.question_type != FormQuestionType.SECTION_HEADER
            and question.question_key not in answered_keys
        ]
        if missing:
            raise VisitFormServiceError(
                "Required form questions are unanswered: " + "; ".join(missing)
            )

    @staticmethod
    def answers_to_out(answers: list[VisitFormAnswer]) -> list[FormAnswerOut]:
        return [
            FormAnswerOut(
                question_key=answer.question_key,
                question_label=answer.question_label,
                question_type=answer.question_type,
                answer=answer.answer_text,
                answer_json=answer.answer_json,
            )
            for answer in answers
        ]

    @staticmethod
    def _has_value(answer: VisitFormAnswer) -> bool:
        if answer.answer_text and answer.answer_text.strip():
            return True
        if answer.answer_json is None:
            return False
        if isinstance(answer.answer_json, list):
            return len(answer.answer_json) > 0
        if isinstance(answer.answer_json, dict):
            return len(answer.answer_json) > 0
        return bool(answer.answer_json)

    def _normalize_answer(
        self, question: VisitFormQuestion, item: FormAnswerIn
    ) -> tuple[str | None, dict | list | None]:
        if question.question_type == FormQuestionType.SECTION_HEADER:
            raise VisitFormServiceError(f"Question '{question.question_key}' is not answerable")

        if question.question_type in (
            FormQuestionType.SINGLE_CHOICE,
            FormQuestionType.TEXT,
            FormQuestionType.TEXTAREA,
            FormQuestionType.RATING_SCALE,
        ):
            if not item.answer or not item.answer.strip():
                return None, None
            if question.question_type == FormQuestionType.SINGLE_CHOICE:
                self._validate_option_value(question, item.answer)
            if question.question_type == FormQuestionType.RATING_SCALE:
                self._validate_rating(question, item.answer)
            return item.answer.strip(), None

        if question.question_type == FormQuestionType.MULTI_CHOICE:
            values = item.answer_json if isinstance(item.answer_json, list) else None
            if values is None and item.answer:
                values = [part.strip() for part in item.answer.split(",") if part.strip()]
            if not values:
                return None, None
            for value in values:
                self._validate_option_value(question, str(value))
            return None, values

        if question.question_type == FormQuestionType.MATRIX:
            if not isinstance(item.answer_json, dict) or not item.answer_json:
                raise VisitFormServiceError(
                    f"Matrix question '{question.question_key}' requires answer_json object"
                )
            self._validate_matrix(question, item.answer_json)
            return None, item.answer_json

        return item.answer, item.answer_json

    @staticmethod
    def _validate_question_payload(
        question_type: FormQuestionType,
        options: list[FormQuestionOptionCreate],
        config: dict | None,
    ) -> None:
        if question_type in (FormQuestionType.SINGLE_CHOICE, FormQuestionType.MULTI_CHOICE):
            if not options:
                raise VisitFormServiceError("Choice questions require at least one option")
        if question_type == FormQuestionType.MATRIX:
            if not config or "rows" not in config or "columns" not in config:
                raise VisitFormServiceError("Matrix questions require config.rows and config.columns")
        if question_type == FormQuestionType.RATING_SCALE:
            if not config or "min" not in config or "max" not in config:
                raise VisitFormServiceError("Rating scale questions require config.min and config.max")

    @staticmethod
    def _validate_option_value(question: VisitFormQuestion, value: str) -> None:
        allowed = {option.value for option in question.options}
        if value not in allowed:
            raise VisitFormServiceError(
                f"Invalid option '{value}' for question '{question.question_key}'"
            )

    @staticmethod
    def _validate_rating(question: VisitFormQuestion, value: str) -> None:
        config = question.config or {}
        minimum = int(config.get("min", 1))
        maximum = int(config.get("max", 5))
        try:
            numeric = int(value)
        except ValueError as exc:
            raise VisitFormServiceError(
                f"Rating for '{question.question_key}' must be a number"
            ) from exc
        if numeric < minimum or numeric > maximum:
            raise VisitFormServiceError(
                f"Rating for '{question.question_key}' must be between {minimum} and {maximum}"
            )

    @staticmethod
    def _validate_matrix(question: VisitFormQuestion, values: dict) -> None:
        config = question.config or {}
        row_keys = {row["key"] for row in config.get("rows", [])}
        column_keys = {col["key"] for col in config.get("columns", [])}
        for row_key, column_value in values.items():
            if row_key not in row_keys:
                raise VisitFormServiceError(f"Unknown matrix row '{row_key}'")
            if str(column_value) not in column_keys:
                raise VisitFormServiceError(
                    f"Invalid matrix value '{column_value}' for row '{row_key}'"
                )

    @staticmethod
    def _to_template_out(template: VisitFormTemplate) -> FormTemplateOut:
        return FormTemplateOut(
            id=template.id,
            name=template.name,
            description=template.description,
            is_active=template.is_active,
            is_default=template.is_default,
            created_at=template.created_at,
            updated_at=template.updated_at,
            questions=[FormQuestionOut.model_validate(q) for q in template.questions],
        )
