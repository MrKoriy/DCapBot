from __future__ import annotations

import asyncio
import logging

import uvloop

uvloop.install()

from aiohttp import web
from aiogram import Bot, Dispatcher

from bot.config import get_settings
from bot.handlers.payment import payment_router
from bot.handlers.user import user_router
from bot.middlewares.db import DbSessionMiddleware
from bot.middlewares.user import UserMiddleware
from bot.webhooks.yookassa import yookassa_webhook_handler


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

    # aiohttp web server for YooKassa webhook
    # In production, nginx reverse-proxies HTTPS (port 443) to port 8080
    app = web.Application()
    app["bot"] = bot
    app.router.add_post("/webhook/yookassa", yookassa_webhook_handler)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)

    logger.info("Bot starting...")
    logger.info("YooKassa webhook server on port 8080")

    # Run polling and webhook server concurrently
    # allowed_updates MUST include "chat_member" for invite link revocation
    await asyncio.gather(
        dp.start_polling(
            bot,
            allowed_updates=["message", "callback_query", "chat_member"],
        ),
        site.start(),
    )


if __name__ == "__main__":
    asyncio.run(main())
