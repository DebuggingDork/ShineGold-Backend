"""
Seed the default super admin user for local development.

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

EMPLOYEE_ID = "ADMIN001"
NAME = "Prasad"
PASSWORD = "shinegold2026"


async def seed_admin() -> None:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.employee_id == EMPLOYEE_ID))
        if result.scalar_one_or_none():
            print(f"Skipped (exists): {EMPLOYEE_ID} — {NAME}")
            return

        db.add(
            User(
                employee_id=EMPLOYEE_ID,
                name=NAME,
                password_hash=hash_password(PASSWORD),
                role=UserRole.SUPER_ADMIN,
            )
        )
        await db.commit()
        print(f"Created super admin: employee_id={EMPLOYEE_ID} password={PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
