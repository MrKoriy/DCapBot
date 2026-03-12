from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, ChatMemberUpdated, Message
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.user import plan_selection_keyboard, status_keyboard
from bot.models.user import User
from bot.repositories.payment import PaymentRepository
from bot.repositories.subscription import SubscriptionRepository

logger = logging.getLogger(__name__)

user_router = Router()


@user_router.message(Command("start"))
async def start_cmd(message: Message, session: AsyncSession, user: User) -> None:
    """Welcome message or subscription status for returning subscribers."""
    sub = await SubscriptionRepository(session).get_active_for_user(user.id)

    if sub is not None:
        await message.answer(
            f"С возвращением!\n"
            f"\n"
            f"Ваша подписка: {sub.plan_name}\n"
            f"Действует до: {sub.expires_at.strftime('%d.%m.%Y')}\n"
            f"Статус: Активна \u2705",
            reply_markup=status_keyboard(),
        )
    else:
        await message.answer(
            "\U0001f44b Добро пожаловать!\n"
            "\n"
            "Это бот для оформления подписки на закрытый канал.\n"
            "\n"
            "Выберите тариф подписки:",
            reply_markup=plan_selection_keyboard(),
        )


@user_router.message(Command("status"))
async def status_cmd(message: Message, session: AsyncSession, user: User) -> None:
    """Show current subscription status."""
    sub = await SubscriptionRepository(session).get_active_for_user(user.id)

    if sub is not None:
        await message.answer(
            f"Ваша подписка: {sub.plan_name}\n"
            f"Действует до: {sub.expires_at.strftime('%d.%m.%Y')}\n"
            f"Статус: Активна \u2705",
            reply_markup=status_keyboard(),
        )
    else:
        await message.answer(
            "У вас нет активной подписки.\n"
            "Используйте /start для оформления подписки.",
        )


@user_router.callback_query(F.data == "payment_history")
async def payment_history_callback(
    callback: CallbackQuery, session: AsyncSession, user: User
) -> None:
    """Show recent payment history."""
    await callback.answer()

    payments = await PaymentRepository(session).get_user_payments(user.id, limit=10)

    if not payments:
        await callback.message.answer("История платежей пуста.")
        return

    lines: list[str] = ["Ваши последние платежи:\n"]
    for p in payments:
        pay_date = (p.confirmed_at or p.created_at).strftime("%d.%m.%Y")
        lines.append(f"- {p.plan_name}: {p.amount} \u20bd ({pay_date})")

    await callback.message.answer("\n".join(lines))


@user_router.callback_query(F.data == "renew")
async def renew_callback(callback: CallbackQuery) -> None:
    """Show plan selection for subscription renewal."""
    await callback.answer()
    await callback.message.answer(
        "Выберите тариф подписки:",
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
