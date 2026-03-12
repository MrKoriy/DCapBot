from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import User


class UserRepository:
    """Data access layer for User model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
    ) -> User:
        """Find or create a user by telegram_id, updating profile fields."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self._session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is not None:
            if user.username != username:
                user.username = username
            if user.first_name != first_name:
                user.first_name = first_name
        else:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                channel_banned=False,
            )
            self._session.add(user)

        await self._session.commit()
        return user
