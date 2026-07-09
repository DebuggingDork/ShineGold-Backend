"""
Seed sample farms assigned to EXEC001 for local development.

Run from backend/:
    uv run python scripts/seed_farms.py
"""
import asyncio
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.enums import FarmStatus, Gender
from app.models.farm import Farm, Farmer
from app.models.user import User

SEED_FARMS = [
    {
        "name": "Green Valley Farm",
        "location_lat": 17.4123,
        "location_lng": 78.4078,
        "location_address": "Gachibowli, Hyderabad",
        "crop": "Tomato",
        "harvest_type": "Kharif",
        "total_acres": 2.5,
        "farmer_name": "Ramesh Kumar",
        "farmer_mobile": "9876500001",
    },
    {
        "name": "Sunrise Acres",
        "location_lat": 17.3616,
        "location_lng": 78.4747,
        "location_address": "Madhapur, Hyderabad",
        "crop": "Chilli",
        "harvest_type": "Rabi",
        "total_acres": 1.8,
        "farmer_name": "Lakshmi Devi",
        "farmer_mobile": "9876500002",
    },
    {
        "name": "River Side Plot",
        "location_lat": 17.4399,
        "location_lng": 78.4983,
        "location_address": "Secunderabad, Telangana",
        "crop": "Cotton",
        "harvest_type": "Kharif",
        "total_acres": 4.0,
        "farmer_name": "Venkat Rao",
        "farmer_mobile": "9876500003",
    },
]


async def seed_farms() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.employee_id == "EXEC001"))
        executive = result.scalar_one_or_none()
        if executive is None:
            print("EXEC001 not found. Run seed_executives.py first.")
            return

        if executive.home_lat is None or executive.home_lng is None:
            executive.home_lat = 17.3850
            executive.home_lng = 78.4867
            executive.address = executive.address or "Hyderabad, Telangana"
            print("Set EXEC001 home location to Hyderabad (17.385, 78.487)")

        harvest_date = date.today() + timedelta(days=60)
        created = 0

        for entry in SEED_FARMS:
            existing = await db.execute(select(Farm).where(Farm.name == entry["name"]))
            if existing.scalar_one_or_none():
                print(f"Skipped (exists): {entry['name']}")
                continue

            farm = Farm(
                name=entry["name"],
                location_lat=entry["location_lat"],
                location_lng=entry["location_lng"],
                location_address=entry["location_address"],
                crop=entry["crop"],
                harvest_type=entry["harvest_type"],
                harvest_date=harvest_date,
                total_acres=entry["total_acres"],
                onboarded_by=executive.id,
                assigned_executive_id=executive.id,
                status=FarmStatus.PENDING_VISIT,
            )
            db.add(farm)
            await db.flush()

            db.add(
                Farmer(
                    farm_id=farm.id,
                    name=entry["farmer_name"],
                    mobile_number=entry["farmer_mobile"],
                    gender=Gender.MALE,
                    age=42,
                )
            )
            created += 1
            print(f"Created farm: {entry['name']} -> assigned to EXEC001")

        await db.commit()
        print(f"Done. Created {created} farm(s) for EXEC001.")


if __name__ == "__main__":
    asyncio.run(seed_farms())
