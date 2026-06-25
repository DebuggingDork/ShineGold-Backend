import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def login(self, employee_id: str, password: str) -> tuple[User, str, str]:
        user = await self.user_repo.get_by_employee_id(employee_id)
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("Invalid employee ID or password")
        if user.is_blocked:
            raise AuthError("This account has been blocked. Contact your admin.")

        access_token = create_access_token(user.id, user.role.value)
        refresh_token = create_refresh_token(user.id)
        return user, access_token, refresh_token

    async def refresh_access_token(self, refresh_token: str) -> str:
        try:
            payload = decode_token(refresh_token)
        except ValueError as e:
            raise AuthError("Invalid or expired refresh token") from e

        if payload.get("type") != "refresh":
            raise AuthError("Invalid token type")

        user = await self.user_repo.get_by_id(uuid.UUID(payload["sub"]))
        if not user or user.is_blocked:
            raise AuthError("User not found or blocked")

        return create_access_token(user.id, user.role.value)

    async def change_password(self, user: User, current_password: str, new_password: str) -> None:
        if not verify_password(current_password, user.password_hash):
            raise AuthError("Current password is incorrect")
        user.password_hash = hash_password(new_password)
        await self.user_repo.update(user)