import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.visit_form import (
    VisitFormAnswer,
    VisitFormQuestion,
    VisitFormQuestionOption,
    VisitFormTemplate,
)
from app.schemas.visit_form import (
    FormQuestionCreate,
    FormQuestionOptionCreate,
    FormQuestionOptionUpdate,
    FormQuestionUpdate,
    FormTemplateCreate,
    FormTemplateUpdate,
)


class VisitFormRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _template_query(self):
        return select(VisitFormTemplate).options(
            selectinload(VisitFormTemplate.questions).selectinload(
                VisitFormQuestion.options
            )
        )

    async def get_template_by_id(self, template_id: uuid.UUID) -> VisitFormTemplate | None:
        result = await self.db.execute(
            self._template_query().where(VisitFormTemplate.id == template_id)
        )
        return result.scalar_one_or_none()

    async def get_active_template(self) -> VisitFormTemplate | None:
        result = await self.db.execute(
            self._template_query()
            .where(VisitFormTemplate.is_active.is_(True))
            .order_by(VisitFormTemplate.updated_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_templates(self) -> list[VisitFormTemplate]:
        result = await self.db.execute(
            select(VisitFormTemplate)
            .options(selectinload(VisitFormTemplate.questions))
            .order_by(VisitFormTemplate.is_active.desc(), VisitFormTemplate.name.asc())
        )
        return list(result.scalars().all())

    async def create_template(self, payload: FormTemplateCreate) -> VisitFormTemplate:
        template = VisitFormTemplate(
            name=payload.name,
            description=payload.description,
            is_active=payload.activate,
            is_default=False,
        )
        self.db.add(template)
        await self.db.flush()
        if payload.activate:
            await self._deactivate_others(template.id)
        await self.db.refresh(template)
        return template

    async def update_template(
        self, template: VisitFormTemplate, payload: FormTemplateUpdate
    ) -> VisitFormTemplate:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(template, field, value)
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def activate_template(self, template: VisitFormTemplate) -> VisitFormTemplate:
        await self._deactivate_others(template.id)
        template.is_active = True
        await self.db.flush()
        await self.db.refresh(template)
        return template

    async def _deactivate_others(self, keep_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(VisitFormTemplate).where(
                VisitFormTemplate.is_active.is_(True),
                VisitFormTemplate.id != keep_id,
            )
        )
        for other in result.scalars().all():
            other.is_active = False
        await self.db.flush()

    async def get_question_by_id(self, question_id: uuid.UUID) -> VisitFormQuestion | None:
        result = await self.db.execute(
            select(VisitFormQuestion)
            .where(VisitFormQuestion.id == question_id)
            .options(selectinload(VisitFormQuestion.options))
        )
        return result.scalar_one_or_none()

    async def create_question(
        self, template: VisitFormTemplate, payload: FormQuestionCreate
    ) -> VisitFormQuestion:
        question = VisitFormQuestion(
            template_id=template.id,
            question_key=payload.question_key,
            label=payload.label,
            help_text=payload.help_text,
            question_type=payload.question_type,
            sort_order=payload.sort_order,
            is_required=payload.is_required,
            config=payload.config,
        )
        self.db.add(question)
        await self.db.flush()

        for option in payload.options:
            self.db.add(
                VisitFormQuestionOption(
                    question_id=question.id,
                    value=option.value,
                    label=option.label,
                    sort_order=option.sort_order,
                )
            )
        await self.db.flush()
        await self.db.refresh(question)
        return question

    async def update_question(
        self, question: VisitFormQuestion, payload: FormQuestionUpdate
    ) -> VisitFormQuestion:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(question, field, value)
        await self.db.flush()
        await self.db.refresh(question)
        return question

    async def delete_question(self, question: VisitFormQuestion) -> None:
        await self.db.delete(question)
        await self.db.flush()

    async def get_option_by_id(self, option_id: uuid.UUID) -> VisitFormQuestionOption | None:
        result = await self.db.execute(
            select(VisitFormQuestionOption).where(VisitFormQuestionOption.id == option_id)
        )
        return result.scalar_one_or_none()

    async def create_option(
        self, question: VisitFormQuestion, payload: FormQuestionOptionCreate
    ) -> VisitFormQuestionOption:
        option = VisitFormQuestionOption(
            question_id=question.id,
            value=payload.value,
            label=payload.label,
            sort_order=payload.sort_order,
        )
        self.db.add(option)
        await self.db.flush()
        await self.db.refresh(option)
        return option

    async def update_option(
        self, option: VisitFormQuestionOption, payload: FormQuestionOptionUpdate
    ) -> VisitFormQuestionOption:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(option, field, value)
        await self.db.flush()
        await self.db.refresh(option)
        return option

    async def delete_option(self, option: VisitFormQuestionOption) -> None:
        await self.db.delete(option)
        await self.db.flush()

    async def count_questions(self, template_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(VisitFormQuestion)
            .where(VisitFormQuestion.template_id == template_id)
        )
        return result.scalar_one()

    async def upsert_visit_answers(
        self,
        visit_id: uuid.UUID,
        answers: list[VisitFormAnswer],
    ) -> None:
        result = await self.db.execute(
            select(VisitFormAnswer).where(VisitFormAnswer.visit_id == visit_id)
        )
        existing = {row.question_key: row for row in result.scalars().all()}
        for answer in answers:
            current = existing.get(answer.question_key)
            if current is not None:
                current.question_label = answer.question_label
                current.question_type = answer.question_type
                current.answer_text = answer.answer_text
                current.answer_json = answer.answer_json
            else:
                self.db.add(answer)
        await self.db.flush()

    async def get_visit_answers(self, visit_id: uuid.UUID) -> list[VisitFormAnswer]:
        result = await self.db.execute(
            select(VisitFormAnswer)
            .where(VisitFormAnswer.visit_id == visit_id)
            .order_by(VisitFormAnswer.question_key.asc())
        )
        return list(result.scalars().all())
