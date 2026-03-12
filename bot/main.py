from __future__ import annotations

import asyncio
import logging

import uvloop

uvloop.install()

from aiogram import Bot, Dispatcher

from bot.config import get_settings
from bot.handlers.payment import payment_router
from bot.handlers.user import user_router
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.user import UserMiddleware


async def main() -> None:
    settings = get_settings()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    bot = Bot(token=settings.bot_token)
    dp = Dispatcher()

    # Middleware chain: DB session (outer) -> user upsert (inner)
    dp.update.outer_middleware(DbSessionMiddleware())
    dp.update.middleware(UserMiddleware())

    dp.include_router(user_router)
    dp.include_router(payment_router)

    logger.info("Bot starting...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
