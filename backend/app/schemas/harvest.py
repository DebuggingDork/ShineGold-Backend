import uuid
from datetime import date

from pydantic import BaseModel


class HarvestFarmSummary(BaseModel):
    id: uuid.UUID
    name: str
    crop: str
    harvest_type: str


class HarvestDayGroup(BaseModel):
    date: date
    farms: list[HarvestFarmSummary]


class HarvestCalendarOut(BaseModel):
    harvests: list[HarvestDayGroup]
