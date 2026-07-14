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


class HarvestReminderItem(BaseModel):
    farm_id: uuid.UUID
    farm_name: str
    crop: str
    harvest_type: str
    harvest_date: date
    remind_on: date
    days_until_harvest: int


class HarvestRemindersOut(BaseModel):
    days_before: int
    items: list[HarvestReminderItem]
