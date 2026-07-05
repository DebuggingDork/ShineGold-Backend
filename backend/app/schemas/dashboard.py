from datetime import date

from pydantic import BaseModel


class AdminDashboardOut(BaseModel):
    total_farms: int
    total_executives: int
    total_visits: int
    farmers_onboarded: int
