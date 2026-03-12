from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user import plan_selection_keyboard
from bot.models.user import User

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
