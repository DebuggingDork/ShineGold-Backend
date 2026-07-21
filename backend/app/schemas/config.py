from pydantic import BaseModel


class AppConfigOut(BaseModel):
    farm_visit_cooldown_days: int
    executive_assignment_radius_km: float
    max_voice_note_seconds: int
