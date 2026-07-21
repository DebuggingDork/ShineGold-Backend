from fastapi import APIRouter

from app.core.config import settings
from app.schemas.config import AppConfigOut

router = APIRouter(prefix="/api/v1/config", tags=["config"])


@router.get("", response_model=AppConfigOut)
async def get_app_config() -> AppConfigOut:
    """Public runtime settings for mobile clients (cooldowns, limits, radii)."""
    return AppConfigOut(
        farm_visit_cooldown_days=settings.FARM_VISIT_COOLDOWN_DAYS,
        executive_assignment_radius_km=settings.EXECUTIVE_ASSIGNMENT_RADIUS_KM,
        max_voice_note_seconds=settings.MAX_VOICE_NOTE_SECONDS,
    )
