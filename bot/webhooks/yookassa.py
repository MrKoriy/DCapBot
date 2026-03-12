from __future__ import annotations

import asyncio
import logging

from aiohttp import web
from aiogram import Bot
from sqlalchemy import select

from bot.config import get_settings
from bot.db.engine import get_session_factory
from bot.models.user import User
from bot.repositories.payment import PaymentRepository
from bot.services.channel import ChannelAccessService
from bot.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)


async def _process_payment(payment_data: dict, bot: Bot) -> None:
    """Process a confirmed payment: activate subscription and send invite link."""
    settings = get_settings()
    session_factory = get_session_factory()

    async with session_factory() as session:
        payment_repo = PaymentRepository(session)
        payment_id = payment_data["id"]

        # Idempotency check -- if already processed, skip
        existing = await payment_repo.find_by_payment_id(payment_id)
        if existing is None:
            logger.warning("Webhook for unknown payment_id=%s, ignoring", payment_id)
            return
        if existing.status == "succeeded":
            logger.info("Duplicate webhook for payment_id=%s, skipping", payment_id)
            return

        # TODO: For production, verify payment via YooKassa API:
        # yk_payment = await asyncio.to_thread(YkPayment.find_one, payment_id)
        # if yk_payment.status != "succeeded": return

        # Mark payment as succeeded
        await payment_repo.mark_succeeded(payment_id)

        # Extract plan info from metadata
        metadata = payment_data.get("metadata", {})
        plan_index = int(metadata.get("plan_index", 0))
        plan = settings.plans[plan_index]

        # Activate subscription
        sub_service = SubscriptionService(session)
        await sub_service.activate(
            user_id=existing.user_id,
            plan_name=plan["name"],
            price=plan["price"],
            days=plan["days"],
        )

        # Get user for invite link flow
        result = await session.execute(
            select(User).where(User.id == existing.user_id)
        )
        user = result.scalar_one_or_none()
        if user is None:
            logger.error(
                "User id=%s not found for payment_id=%s",
                existing.user_id,
                payment_id,
            )
            await session.commit()
            return

        # Issue invite link (handles unban-before-invite)
        channel_service = ChannelAccessService(bot, session)
        invite_link = await channel_service.issue_invite(user)
        await channel_service.send_invite_to_user(user, invite_link)

        await session.commit()
        logger.info(
            "Payment %s processed: subscription activated, invite sent to user %s",
            payment_id,
            user.telegram_id,
        )


async def yookassa_webhook_handler(request: web.Request) -> web.Response:
    """Handle YooKassa webhook notification. Respond 200 immediately, process async."""
    try:
        body = await request.json()
    except Exception:
        return web.Response(status=400)

    event_type = body.get("event")
    if event_type != "payment.succeeded":
        # We only care about successful payments. Return 200 to stop YooKassa retries.
        return web.Response(status=200)

    payment_data = body.get("object", {})
    bot = request.app["bot"]

    # Fire and forget -- respond 200 immediately to YooKassa
    asyncio.create_task(_process_payment(payment_data, bot))
    return web.Response(status=200)
