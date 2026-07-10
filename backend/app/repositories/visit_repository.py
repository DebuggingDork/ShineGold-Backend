import uuid
from datetime import date, datetime, time, timezone

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import FarmStatus, VisitStatus
from app.models.farm import Farm
from app.models.visit import Visit, VisitMcqAnswer, VisitPhoto
from app.schemas.visit import (
    McqAnswerOut,
    VisitDetailOut,
    VisitExecutiveSummary,
    VisitFarmSummary,
    VisitFormUpdate,
    VisitHistoryItem,
    VisitMineItem,
    VisitPhotoOut,
)


from app.services.visit_form_service import VisitFormService


def _remarks_preview(text: str | None, limit: int = 120) -> str | None:
    if not text:
        return None
    cleaned = text.strip()
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[:limit].rstrip() + "..."


class VisitRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, visit_id: uuid.UUID) -> Visit | None:
        result = await self.db.execute(
            select(Visit)
            .where(Visit.id == visit_id)
            .options(
                selectinload(Visit.photos),
                selectinload(Visit.mcq_answers),
                selectinload(Visit.form_answers),
                selectinload(Visit.farm).selectinload(Farm.farmer),
                selectinload(Visit.executive),
            )
        )
        return result.scalar_one_or_none()

    async def get_in_progress_for_executive(self, executive_id: uuid.UUID) -> Visit | None:
        result = await self.db.execute(
            select(Visit).where(
                Visit.executive_id == executive_id,
                Visit.status == VisitStatus.IN_PROGRESS,
            )
        )
        return result.scalar_one_or_none()

    async def create_checkin(
        self,
        farm_id: uuid.UUID,
        executive_id: uuid.UUID,
        checkin_lat: float,
        checkin_lng: float,
    ) -> Visit:
        visit = Visit(
            farm_id=farm_id,
            executive_id=executive_id,
            checkin_lat=checkin_lat,
            checkin_lng=checkin_lng,
            status=VisitStatus.IN_PROGRESS,
        )
        self.db.add(visit)
        await self.db.flush()
        await self.db.refresh(visit)
        return visit

    async def update_form(self, visit: Visit, payload: VisitFormUpdate) -> list[str]:
        updated_fields: list[str] = []

        if payload.photos is not None:
            visit.photos = [
                VisitPhoto(
                    visit_id=visit.id,
                    photo_url=photo.photo_url,
                    captured_lat=photo.captured_lat,
                    captured_lng=photo.captured_lng,
                    captured_at=photo.captured_at,
                )
                for photo in payload.photos
            ]
            updated_fields.append("photos")

        if payload.voice_note_url is not None:
            visit.voice_note_url = payload.voice_note_url
            updated_fields.append("voice_note_url")

        if payload.text_note is not None:
            visit.text_note = payload.text_note
            updated_fields.append("text_note")

        if payload.mcq_answers is not None:
            answers_by_key = {answer.question_key: answer for answer in visit.mcq_answers}
            for mcq in payload.mcq_answers:
                existing = answers_by_key.get(mcq.question_key)
                if existing is not None:
                    existing.answer = mcq.answer
                else:
                    visit.mcq_answers.append(
                        VisitMcqAnswer(
                            visit_id=visit.id,
                            question_key=mcq.question_key,
                            answer=mcq.answer,
                        )
                    )
            updated_fields.append("mcq_answers")

        if payload.form_answers is not None:
            form_service = VisitFormService(self.db)
            form_fields = await form_service.save_visit_answers(visit, payload.form_answers)
            updated_fields.extend(form_fields)

            action_plan = next(
                (item.answer for item in payload.form_answers if item.question_key == "action_plan"),
                None,
            )
            if action_plan is not None:
                visit.text_note = action_plan

        await self.db.flush()
        await self.db.refresh(visit)
        return updated_fields

    async def cancel(self, visit: Visit) -> Visit:
        visit.status = VisitStatus.CANCELLED
        await self.db.flush()
        await self.db.refresh(visit)
        return visit

    async def submit(
        self,
        visit: Visit,
        checkout_lat: float,
        checkout_lng: float,
    ) -> Visit:
        checkout_time = datetime.now(timezone.utc)
        checkin_time = visit.checkin_time
        if checkin_time.tzinfo is None:
            checkin_time = checkin_time.replace(tzinfo=timezone.utc)

        visit.checkout_lat = checkout_lat
        visit.checkout_lng = checkout_lng
        visit.checkout_time = checkout_time
        visit.duration_seconds = max(0, int((checkout_time - checkin_time).total_seconds()))
        visit.status = VisitStatus.COMPLETED

        if visit.farm.status == FarmStatus.PENDING_VISIT:
            visit.farm.status = FarmStatus.VISITED

        await self.db.flush()
        await self.db.refresh(visit)
        return visit

    async def list_mine(
        self,
        executive_id: uuid.UUID,
        *,
        status: VisitStatus | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        farm_name: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Visit], int]:
        filters = [Visit.executive_id == executive_id]

        if status is not None:
            filters.append(Visit.status == status)
        if date_from is not None:
            filters.append(
                Visit.checkin_time
                >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
            )
        if date_to is not None:
            filters.append(
                Visit.checkin_time
                <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
            )
        if farm_name:
            filters.append(Farm.name.ilike(f"%{farm_name}%"))

        base_query = (
            select(Visit)
            .join(Farm, Farm.id == Visit.farm_id)
            .where(and_(*filters))
            .options(selectinload(Visit.farm), selectinload(Visit.photos))
            .order_by(Visit.checkin_time.desc())
        )
        count_query = (
            select(func.count(func.distinct(Visit.id)))
            .select_from(Visit)
            .join(Farm, Farm.id == Visit.farm_id)
            .where(and_(*filters))
        )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        result = await self.db.execute(
            base_query.offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().unique().all()), total

    async def list_for_farm(
        self,
        farm_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Visit], int]:
        filters = [
            Visit.farm_id == farm_id,
            Visit.status == VisitStatus.COMPLETED,
        ]
        base_query = (
            select(Visit)
            .where(and_(*filters))
            .options(
                selectinload(Visit.farm),
                selectinload(Visit.photos),
                selectinload(Visit.executive),
            )
            .order_by(Visit.checkout_time.desc(), Visit.checkin_time.desc())
        )
        count_query = (
            select(func.count())
            .select_from(Visit)
            .where(and_(*filters))
        )

        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        result = await self.db.execute(
            base_query.offset((page - 1) * page_size).limit(page_size)
        )
        return list(result.scalars().unique().all()), total

    async def get_latest_completed_for_farm(self, farm_id: uuid.UUID) -> Visit | None:
        result = await self.db.execute(
            select(Visit)
            .where(Visit.farm_id == farm_id, Visit.status == VisitStatus.COMPLETED)
            .options(
                selectinload(Visit.photos),
                selectinload(Visit.mcq_answers),
                selectinload(Visit.form_answers),
                selectinload(Visit.farm),
                selectinload(Visit.executive),
            )
            .order_by(Visit.checkout_time.desc(), Visit.checkin_time.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def to_mine_item(visit: Visit) -> VisitMineItem:
        return VisitMineItem(
            visit_id=visit.id,
            farm=VisitFarmSummary(id=visit.farm.id, name=visit.farm.name),
            status=visit.status,
            checkin_time=visit.checkin_time,
            checkout_time=visit.checkout_time,
            duration_seconds=visit.duration_seconds,
            remarks_preview=_remarks_preview(visit.text_note),
            has_voice_note=bool(visit.voice_note_url),
            photo_count=len(visit.photos),
        )

    @staticmethod
    def to_history_item(visit: Visit) -> VisitHistoryItem:
        return VisitHistoryItem(
            visit_id=visit.id,
            farm_id=visit.farm_id,
            farm_name=visit.farm.name,
            status=visit.status,
            checkin_time=visit.checkin_time,
            checkout_time=visit.checkout_time,
            duration_seconds=visit.duration_seconds,
            remarks_preview=_remarks_preview(visit.text_note),
            has_voice_note=bool(visit.voice_note_url),
            photo_count=len(visit.photos),
            visited_by=VisitExecutiveSummary(
                id=visit.executive.id,
                name=visit.executive.name,
            ),
        )

    @staticmethod
    def to_detail(visit: Visit) -> VisitDetailOut:
        return VisitDetailOut(
            visit_id=visit.id,
            farm_id=visit.farm_id,
            farm_name=visit.farm.name,
            status=visit.status,
            checkin_time=visit.checkin_time,
            checkout_time=visit.checkout_time,
            duration_seconds=visit.duration_seconds,
            text_note=visit.text_note,
            photos=[VisitPhotoOut.model_validate(photo) for photo in visit.photos],
            voice_note_url=visit.voice_note_url,
            mcq_answers=[
                McqAnswerOut(question_key=answer.question_key, answer=answer.answer)
                for answer in visit.mcq_answers
            ],
            form_answers=VisitFormService.answers_to_out(list(visit.form_answers)),
            visited_by=VisitExecutiveSummary(
                id=visit.executive.id,
                name=visit.executive.name,
            ),
            has_voice_note=bool(visit.voice_note_url),
            has_photos=bool(visit.photos),
        )
