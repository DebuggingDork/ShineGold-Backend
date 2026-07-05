from datetime import date
import uuid

from pydantic import BaseModel


class AdminDashboardOut(BaseModel):
    total_farms: int
    total_executives: int
    total_visits: int
    farmers_onboarded: int


class UpcomingHarvest(BaseModel):
    farm_id: uuid.UUID
    farm_name: str
    harvest_date: date


class ExecutiveDashboardOut(BaseModel):
    greeting_name: str
    date: date
    total_farms_to_visit: int
    upcoming_harvests: list[UpcomingHarvest]
    farms_visited_count: int
    pending_farms_count: int
