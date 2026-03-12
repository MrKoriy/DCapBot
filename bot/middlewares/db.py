from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from bot.db.engine import get_session_factory


class DbSessionMiddleware(BaseMiddleware):
    """Outer middleware that injects an async DB session into handler data."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        session_factory = get_session_factory()
        async with session_factory() as session:
            data["session"] = session
            return await handler(event, data)
