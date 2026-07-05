import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import FarmStatus, VisitStatus
from app.models.visit import Visit, VisitMcqAnswer, VisitPhoto
from app.schemas.visit import VisitFormUpdate


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
                selectinload(Visit.farm),
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

        await self.db.flush()
        await self.db.refresh(visit)
        return updated_fields

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
