"""
Seed Shinegold executive users from Executive Details CSV.

How to run (from backend/):
    uv run python scripts/seed_executives.py

Or with the project venv activated:
    python scripts/seed_executives.py

Default password for every executive:
    ChangeMe123!

Login with employee_id + password, e.g.:
    EXEC001 / ChangeMe123!
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.user import User

DEFAULT_PASSWORD = "ChangeMe123!"

# Real executive details from Executive Details_Shinegold.csv
SEED_EXECUTIVES: list[dict] = [
    {
        "employee_id": "EXEC001",
        "name": "G. Muddugangappa",
        "password": DEFAULT_PASSWORD,
        "mobile_number": "9902029987",
        "address": "Maraluru, Ramapura, Kasaba, Gowribidanur, Chikka Ballapura, 561208",
    },
    {
        "employee_id": "EXEC002",
        "name": "Narasimhamurthy",
        "password": DEFAULT_PASSWORD,
        "mobile_number": "9901451502",
        "address": "G Bommasandr, Gowribidanur, Chikka Ballapur, 561213",
    },
    {
        "employee_id": "EXEC003",
        "name": "Pillegowda YB",
        "password": DEFAULT_PASSWORD,
        "mobile_number": "9742009060",
        "address": "Yeliyur, Devanahalli, Bangalore Rural, 562110",
    },
    {
        "employee_id": "EXEC004",
        "name": "R Ranganna",
        "password": DEFAULT_PASSWORD,
        "mobile_number": "9740037313",
        "address": "Subrigistar Official Building, Vinayaka Nagara, Pavagada, Tumkur, 561202",
    },
]


async def seed_executives() -> None:
    async with AsyncSessionLocal() as db:
        for entry in SEED_EXECUTIVES:
            result = await db.execute(
                select(User).where(User.employee_id == entry["employee_id"])
            )
            if result.scalar_one_or_none():
                print(f"Skipped (exists): {entry['employee_id']} — {entry['name']}")
                continue

            db.add(
                User(
                    employee_id=entry["employee_id"],
                    name=entry["name"],
                    password_hash=hash_password(entry["password"]),
                    role=UserRole.EXECUTIVE,
                    mobile_number=entry.get("mobile_number"),
                    address=entry.get("address"),
                )
            )
            await db.flush()
            print(
                f"Created executive: employee_id={entry['employee_id']} "
                f"password={entry['password']}"
            )

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_executives())
