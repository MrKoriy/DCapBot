from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import ChatMemberUpdated, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user import plan_selection_keyboard
from bot.models.user import User

logger = logging.getLogger(__name__)

user_router = Router()


@user_router.message(Command("start"))
async def start_cmd(message: Message, session: AsyncSession, user: User) -> None:
    """Welcome message with subscription plan selection keyboard."""
    await message.answer(
        "\U0001f44b \u0414\u043e\u0431\u0440\u043e \u043f\u043e\u0436\u0430\u043b\u043e\u0432\u0430\u0442\u044c!\n"
        "\n"
        "\u042d\u0442\u043e \u0431\u043e\u0442 \u0434\u043b\u044f \u043e\u0444\u043e\u0440\u043c\u043b\u0435\u043d\u0438\u044f \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0438 \u043d\u0430 \u0437\u0430\u043a\u0440\u044b\u0442\u044b\u0439 \u043a\u0430\u043d\u0430\u043b.\n"
        "\n"
        "\u0412\u044b\u0431\u0435\u0440\u0438\u0442\u0435 \u0442\u0430\u0440\u0438\u0444 \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0438:",
        reply_markup=plan_selection_keyboard(),
    )


@user_router.chat_member(F.new_chat_member.status == "member")
async def on_user_joined(event: ChatMemberUpdated) -> None:
    """Revoke invite link when user joins via one-time link."""
    if event.invite_link is not None:
        try:
            await event.bot.revoke_chat_invite_link(
                chat_id=event.chat.id,
                invite_link=event.invite_link.invite_link,
            )
            logger.info(
                "Revoked invite link for user %s",
                event.new_chat_member.user.id,
            )
        except Exception as e:
            logger.warning("Failed to revoke invite link: %s", e)
