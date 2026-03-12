from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.models.user import User
from bot.services.payment import PaymentService

logger = logging.getLogger(__name__)

payment_router = Router()


@payment_router.callback_query(F.data.startswith("plan:"))
async def plan_selected(callback: CallbackQuery, session: AsyncSession, user: User) -> None:
    """Handle plan button tap: create YooKassa payment and send payment link."""
    settings = get_settings()

    raw_index = callback.data.split(":")[1]
    try:
        plan_index = int(raw_index)
    except (ValueError, IndexError):
        await callback.answer("Некорректный выбор тарифа.", show_alert=True)
        return

    if plan_index < 0 or plan_index >= len(settings.plans):
        await callback.answer("Тариф не найден.", show_alert=True)
        return

    # Acknowledge the callback immediately to remove the loading spinner
    await callback.answer()

    try:
        service = PaymentService(session)
        payment_url = await service.create_payment(user, plan_index, settings.bot_username)
    except Exception:
        logger.exception("Failed to create YooKassa payment for user %s", user.telegram_id)
        await callback.message.answer(
            "Произошла ошибка при создании платежа. Попробуйте позже."
        )
        return

    plan = settings.plans[plan_index]
    builder = InlineKeyboardBuilder()
    builder.button(text="Оплатить", url=payment_url)
    await callback.message.answer(
        f"Оплата подписки: {plan['name']}\n"
        f"Сумма: {plan['price']} \u20bd\n\n"
        "Нажмите кнопку ниже для оплаты:",
        reply_markup=builder.as_markup(),
    )
