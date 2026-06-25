"""
Seed sample executive users for local development.

Run from backend/:
    uv run python scripts/seed_executives.py
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

SEED_EXECUTIVES: list[dict] = [
    {
        "employee_id": "EXEC001",
        "name": "Executive One",
        "password": DEFAULT_PASSWORD,
        "mobile_number": "9876543210",
        "address": "Hyderabad, Telangana",
    },
    {
        "employee_id": "EXEC002",
        "name": "Executive Two",
        "password": DEFAULT_PASSWORD,
        "mobile_number": "9876543211",
        "address": "Warangal, Telangana",
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
