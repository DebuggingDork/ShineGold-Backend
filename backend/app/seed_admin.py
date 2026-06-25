"""
One-off script to create the first super admin user.
Run with: uv run python -m app.seed_admin
"""
import asyncio

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.enums import UserRole
from app.models.user import User


async def seed_admin():
    async with AsyncSessionLocal() as db:
        admin = User(
            employee_id="ADMIN001",
            name="Super Admin",
            password_hash=hash_password("ChangeMe123!"),
            role=UserRole.SUPER_ADMIN,
        )
        db.add(admin)
        await db.commit()
        print(f"Created super admin: employee_id=ADMIN001 password=ChangeMe123!")


if __name__ == "__main__":
    asyncio.run(seed_admin())