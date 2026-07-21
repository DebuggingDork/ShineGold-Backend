from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.models.enums import FarmStatus


class FarmVisitService:
    @staticmethod
    def cooldown_cutoff(*, now: datetime | None = None) -> datetime:
        current = now or datetime.now(timezone.utc)
        if current.tzinfo is None:
            current = current.replace(tzinfo=timezone.utc)
        return current - timedelta(days=settings.FARM_VISIT_COOLDOWN_DAYS)

    @staticmethod
    def _normalize_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def effective_farm_status(
        stored_status: FarmStatus,
        last_visited: datetime | None,
        *,
        now: datetime | None = None,
    ) -> FarmStatus:
        """Return the visit status clients should use (includes revisit cooldown)."""
        if stored_status != FarmStatus.VISITED:
            return stored_status

        if last_visited is None:
            return FarmStatus.PENDING_VISIT

        last = FarmVisitService._normalize_utc(last_visited)
        cutoff = FarmVisitService.cooldown_cutoff(now=now)
        if last <= cutoff:
            return FarmStatus.PENDING_VISIT
        return FarmStatus.VISITED

    @staticmethod
    def is_due_for_visit(
        stored_status: FarmStatus,
        last_visited: datetime | None,
        *,
        now: datetime | None = None,
    ) -> bool:
        return (
            FarmVisitService.effective_farm_status(
                stored_status,
                last_visited,
                now=now,
            )
            == FarmStatus.PENDING_VISIT
        )

    @staticmethod
    def is_in_visit_cooldown(
        stored_status: FarmStatus,
        last_visited: datetime | None,
        *,
        now: datetime | None = None,
    ) -> bool:
        return stored_status == FarmStatus.VISITED and not FarmVisitService.is_due_for_visit(
            stored_status,
            last_visited,
            now=now,
        )

    @staticmethod
    def next_visit_available_at(
        stored_status: FarmStatus,
        last_visited: datetime | None,
        *,
        now: datetime | None = None,
    ) -> datetime | None:
        if not FarmVisitService.is_in_visit_cooldown(
            stored_status, last_visited, now=now
        ):
            return None
        if last_visited is None:
            return None
        last = FarmVisitService._normalize_utc(last_visited)
        return last + timedelta(days=settings.FARM_VISIT_COOLDOWN_DAYS)

    @staticmethod
    def visit_response_fields(
        stored_status: FarmStatus,
        last_visited: datetime | None,
        *,
        now: datetime | None = None,
    ) -> dict:
        return {
            "status": FarmVisitService.effective_farm_status(
                stored_status, last_visited, now=now
            ),
            "next_visit_available_at": FarmVisitService.next_visit_available_at(
                stored_status, last_visited, now=now
            ),
            "visit_cooldown_days": settings.FARM_VISIT_COOLDOWN_DAYS,
        }

    @staticmethod
    def cooldown_message() -> str:
        days = settings.FARM_VISIT_COOLDOWN_DAYS
        unit = "day" if days == 1 else "days"
        return (
            f"This farm was visited recently. "
            f"Please wait {days} {unit} between visits."
        )
