"""
Seed super admin users.

Run from backend/:
    uv run python scripts/seed_admin.py
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

SEED_ADMINS: list[dict] = [
    {
        "employee_id": "ADMIN001",
        "name": "Prasad",
        "password": "shinegold2026",
    },
    {
        "employee_id": "ADMIN135",
        "name": "Mani Mamidala",
        "password": "Idk@1355",
    },
]


async def seed_admins() -> None:
    async with AsyncSessionLocal() as db:
        for entry in SEED_ADMINS:
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
                    role=UserRole.SUPER_ADMIN,
                )
            )
            await db.flush()
            print(
                f"Created super admin: employee_id={entry['employee_id']} "
                f"password={entry['password']}"
            )

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_admins())
