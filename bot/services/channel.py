from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from aiogram import Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.models.user import User

logger = logging.getLogger(__name__)


class ChannelAccessService:
    """Manages channel invite link lifecycle: issue, send, revoke."""

    def __init__(self, bot: Bot, session: AsyncSession) -> None:
        self._bot = bot
        self._session = session

    async def issue_invite(self, user: User) -> str:
        """Generate a one-time invite link. Unbans user first if they were banned."""
        settings = get_settings()

        # CRITICAL: Unban-before-invite pattern (Pitfall 1 from research)
        if user.channel_banned:
            await self._bot.unban_chat_member(
                chat_id=settings.channel_id,
                user_id=user.telegram_id,
                only_if_banned=True,
            )
            user.channel_banned = False
            await self._session.flush()
            # Small delay so Telegram processes the unban before invite generation
            await asyncio.sleep(1)

        expire_date = datetime.now(timezone.utc) + timedelta(hours=1)
        link = await self._bot.create_chat_invite_link(
            chat_id=settings.channel_id,
            member_limit=1,
            expire_date=expire_date,
            name=f"user_{user.telegram_id}",
        )
        return link.invite_link

    async def revoke_invite(self, invite_link: str) -> None:
        """Revoke an invite link. Silently handles already-expired/revoked links."""
        settings = get_settings()
        try:
            await self._bot.revoke_chat_invite_link(
                chat_id=settings.channel_id,
                invite_link=invite_link,
            )
        except Exception as exc:
            logger.warning("Failed to revoke invite link: %s", exc)

    async def kick_user(self, user: User) -> None:
        """Kick user from channel (ban + immediate unban so they can rejoin later)."""
        settings = get_settings()
        await self._bot.ban_chat_member(
            chat_id=settings.channel_id,
            user_id=user.telegram_id,
        )
        await self._bot.unban_chat_member(
            chat_id=settings.channel_id,
            user_id=user.telegram_id,
            only_if_banned=True,
        )
        user.channel_banned = True
        await self._session.flush()
        logger.info("Kicked user %s (telegram_id=%d) from channel", user.username, user.telegram_id)

    async def send_expiry_notification(self, user: User) -> None:
        """Notify user that their subscription has expired."""
        try:
            await self._bot.send_message(
                chat_id=user.telegram_id,
                text="Ваша подписка истекла. Чтобы продлить доступ, используйте /start.",
            )
        except Exception as exc:
            logger.warning("Failed to send expiry notification to %d: %s", user.telegram_id, exc)

    async def send_reminder(self, user: User, expires_at: datetime) -> None:
        """Send a reminder that the subscription is expiring soon."""
        try:
            await self._bot.send_message(
                chat_id=user.telegram_id,
                text=(
                    f"Ваша подписка истекает {expires_at.strftime('%d.%m.%Y')}. "
                    "Чтобы продлить, используйте /start."
                ),
            )
        except Exception as exc:
            logger.warning("Failed to send reminder to %d: %s", user.telegram_id, exc)

    async def send_invite_to_user(self, user: User, invite_link: str) -> None:
        """Send the invite link to the user as an inline button."""
        builder = InlineKeyboardBuilder()
        builder.button(text="Вступить в канал", url=invite_link)

        await self._bot.send_message(
            chat_id=user.telegram_id,
            text=(
                "Оплата подтверждена! Спасибо за подписку.\n\n"
                "Нажмите кнопку ниже, чтобы вступить в канал.\n"
                "Ссылка действительна 1 час и рассчитана на одного человека."
            ),
            reply_markup=builder.as_markup(),
        )
