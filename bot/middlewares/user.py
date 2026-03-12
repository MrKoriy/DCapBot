from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from sqlalchemy.ext.asyncio import AsyncSession

from bot.repositories.user import UserRepository


class UserMiddleware(BaseMiddleware):
    """Inner middleware that upserts the user record on every interaction."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        event_user = data.get("event_from_user")
        if event_user is None:
            return await handler(event, data)

        session: AsyncSession = data["session"]
        repo = UserRepository(session)
        user = await repo.upsert(
            telegram_id=event_user.id,
            username=event_user.username,
            first_name=event_user.first_name,
        )
        data["user"] = user
        return await handler(event, data)
