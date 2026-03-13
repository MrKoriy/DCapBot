from __future__ import annotations

import asyncio
import logging
from aiohttp import web
from aiogram import Bot
from sqlalchemy import select
from yookassa import Configuration
from yookassa import Payment as YkPayment

from bot.config import get_settings
from bot.db.engine import get_session_factory
from bot.models.user import User
from bot.repositories.payment import PaymentRepository
from bot.services.channel import ChannelAccessService
from bot.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)


def _resolve_plan_by_name(plan_name: str) -> dict | None:
    """Find a plan in settings by its name."""
    settings = get_settings()
    for plan in settings.plans:
        if plan["name"] == plan_name:
            return plan
    return None


async def _process_payment(payment_id: str, bot: Bot) -> None:
    """Process a confirmed payment: verify via API, activate subscription, send invite."""
    settings = get_settings()
    session_factory = get_session_factory()

    # Server-side verification: confirm payment status directly with YooKassa
    Configuration.account_id = settings.yookassa_shop_id
    Configuration.secret_key = settings.yookassa_secret_key
    yk_payment = await asyncio.to_thread(YkPayment.find_one, payment_id)
    if yk_payment.status != "succeeded":
        logger.warning(
            "YooKassa API says payment_id=%s status=%s, skipping",
            payment_id,
            yk_payment.status,
        )
        return

    async with session_factory() as session:
        payment_repo = PaymentRepository(session)

        # Idempotency check -- if already processed, skip
        existing = await payment_repo.find_by_payment_id(payment_id)
        if existing is None:
            logger.warning("Webhook for unknown payment_id=%s, ignoring", payment_id)
            return
        if existing.status == "succeeded":
            logger.info("Duplicate webhook for payment_id=%s, skipping", payment_id)
            return

        # Mark payment as succeeded
        await payment_repo.mark_succeeded(payment_id)

        # Use plan data from the local DB record (not from webhook metadata)
        plan = _resolve_plan_by_name(existing.plan_name)
        if plan is None:
            logger.error(
                "Unknown plan_name=%s for payment_id=%s",
                existing.plan_name,
                payment_id,
            )
            await session.commit()
            return

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
    payment_id = payment_data.get("id")
    if not payment_id:
        return web.Response(status=400)

    bot = request.app["bot"]

    # Fire and forget -- respond 200 immediately to YooKassa
    asyncio.create_task(_process_payment(payment_id, bot))
    return web.Response(status=200)
