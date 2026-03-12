from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import get_settings
from bot.db.engine import get_session_factory
from bot.repositories.subscription import SubscriptionRepository
from bot.services.channel import ChannelAccessService
from bot.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """Create and configure APScheduler with persistent SQLAlchemy job store."""
    settings = get_settings()

    jobstores = {
        "default": SQLAlchemyJobStore(url=settings.database_url_sync),
    }
    scheduler = AsyncIOScheduler(jobstores=jobstores)

    scheduler.add_job(
        check_expired_subscriptions,
        "interval",
        hours=1,
        args=[bot],
        id="check_expired_subscriptions",
        replace_existing=True,
    )
    scheduler.add_job(
        send_expiry_reminders,
        "interval",
        hours=1,
        args=[bot],
        id="send_expiry_reminders",
        replace_existing=True,
    )
    scheduler.add_job(
        sweep_ghost_members,
        "interval",
        hours=6,
        args=[bot],
        id="sweep_ghost_members",
        replace_existing=True,
    )

    return scheduler


async def check_expired_subscriptions(bot: Bot) -> None:
    """Find expired-but-active subscriptions: kick user, notify, mark expired."""
    logger.info("Running check_expired_subscriptions...")
    session_factory = get_session_factory()

    try:
        async with session_factory() as session:
            repo = SubscriptionRepository(session)
            svc = SubscriptionService(session)
            channel = ChannelAccessService(bot, session)

            expired = await repo.get_expired_active()
            logger.info("Found %d expired subscriptions", len(expired))

            for sub in expired:
                try:
                    await channel.kick_user(sub.user)
                    await channel.send_expiry_notification(sub.user)
                    await svc.expire_subscription(sub)
                    await session.commit()
                    logger.info(
                        "Expired subscription %d for user %d",
                        sub.id,
                        sub.user.telegram_id,
                    )
                except Exception:
                    logger.exception("Error expiring subscription %d", sub.id)
                    await session.rollback()

                await asyncio.sleep(0.5)

    except Exception:
        logger.exception("check_expired_subscriptions failed")


async def send_expiry_reminders(bot: Bot) -> None:
    """Send reminders to users whose subscriptions expire within 3 days."""
    logger.info("Running send_expiry_reminders...")
    session_factory = get_session_factory()

    try:
        async with session_factory() as session:
            repo = SubscriptionRepository(session)
            channel = ChannelAccessService(bot, session)

            expiring = await repo.get_expiring_soon(days=3)
            logger.info("Found %d subscriptions expiring soon", len(expiring))

            for sub in expiring:
                try:
                    await channel.send_reminder(sub.user, sub.expires_at)
                    sub.reminder_sent = True
                    await session.commit()
                    logger.info(
                        "Sent reminder for subscription %d to user %d",
                        sub.id,
                        sub.user.telegram_id,
                    )
                except Exception:
                    logger.exception("Error sending reminder for subscription %d", sub.id)
                    await session.rollback()

                await asyncio.sleep(0.5)

    except Exception:
        logger.exception("send_expiry_reminders failed")


async def sweep_ghost_members(bot: Bot) -> None:
    """Check channel for members without active subscriptions and kick them."""
    logger.info("Running sweep_ghost_members...")
    settings = get_settings()
    session_factory = get_session_factory()

    try:
        async with session_factory() as session:
            repo = SubscriptionRepository(session)
            channel = ChannelAccessService(bot, session)

            ghosts = await repo.get_users_without_active_sub()
            logger.info("Found %d potential ghost members to check", len(ghosts))

            for user in ghosts:
                try:
                    member = await bot.get_chat_member(
                        chat_id=settings.channel_id,
                        user_id=user.telegram_id,
                    )
                    if member.status == "member":
                        await channel.kick_user(user)
                        await session.commit()
                        logger.info(
                            "Swept ghost member %d from channel",
                            user.telegram_id,
                        )
                except Exception:
                    logger.exception(
                        "Error checking/sweeping ghost member %d", user.telegram_id
                    )
                    await session.rollback()

                await asyncio.sleep(0.5)

    except Exception:
        logger.exception("sweep_ghost_members failed")


async def startup_reconciliation(bot: Bot) -> None:
    """Run expired subscription check on startup to catch anything missed while offline."""
    logger.info("Running startup reconciliation...")
    await check_expired_subscriptions(bot)
    logger.info("Startup reconciliation complete")
