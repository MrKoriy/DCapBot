from __future__ import annotations

import logging
import math
from datetime import timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.keyboards.admin import (
    admin_menu_keyboard,
    grant_plan_keyboard,
    manage_subscription_keyboard,
    subscribers_pagination_keyboard,
)
from bot.models.user import User
from bot.repositories.admin import AdminRepository
from bot.repositories.subscription import SubscriptionRepository
from bot.services.channel import ChannelAccessService
from bot.services.subscription import SubscriptionService

logger = logging.getLogger(__name__)

admin_router = Router()

PER_PAGE = 10


class AdminGrant(StatesGroup):
    """FSM states for the admin grant subscription flow."""
    waiting_for_user = State()
    waiting_for_plan = State()


def _is_admin(user_id: int) -> bool:
    return user_id in get_settings().admin_ids


def _back_menu_keyboard() -> InlineKeyboardMarkup:
    """Single 'back to menu' button."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад в меню", callback_data="adm:menu")
    builder.adjust(1)
    return builder.as_markup()


def _format_subscriber_line(user: User, sub: "Subscription") -> str:  # noqa: F821
    """Format one subscriber line for the list."""
    if user.username:
        name = f"@{user.username}"
    elif user.first_name:
        name = user.first_name
    else:
        name = str(user.telegram_id)
    expires = sub.expires_at.strftime("%d.%m.%Y")
    return f"{name} | {sub.plan_name} | до {expires}"


async def _render_subscribers_page(
    callback: CallbackQuery, session: AsyncSession, page: int
) -> None:
    """Shared logic for rendering a subscribers page."""
    repo = AdminRepository(session)
    rows, total = await repo.get_subscribers_page(page=page, per_page=PER_PAGE)
    total_pages = max(1, math.ceil(total / PER_PAGE))

    if not rows:
        text = "Нет активных подписчиков."
    else:
        lines = [f"Подписчики ({total}):\n"]
        for user, sub in rows:
            lines.append(_format_subscriber_line(user, sub))
        text = "\n".join(lines)

    await callback.message.edit_text(
        text, reply_markup=subscribers_pagination_keyboard(page, total_pages)
    )


@admin_router.message(Command("admin"))
async def admin_cmd(message: Message) -> None:
    """Show admin panel main menu."""
    if not _is_admin(message.from_user.id):
        return
    await message.answer(
        "Панель администратора:", reply_markup=admin_menu_keyboard()
    )


@admin_router.callback_query(F.data == "adm:menu")
async def admin_menu_callback(callback: CallbackQuery) -> None:
    """Return to admin panel main menu."""
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer()
    await callback.message.edit_text(
        "Панель администратора:", reply_markup=admin_menu_keyboard()
    )


@admin_router.callback_query(F.data == "adm:subscribers")
async def subscribers_callback(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Show first page of active subscribers."""
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer()
    await _render_subscribers_page(callback, session, page=0)


@admin_router.callback_query(F.data.startswith("adm:subs:"))
async def subscribers_page_callback(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Show specific page of active subscribers."""
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer()
    page = int(callback.data.split(":")[-1])
    await _render_subscribers_page(callback, session, page=page)


@admin_router.callback_query(F.data == "adm:stats")
async def stats_callback(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Show subscription statistics."""
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer()

    stats = await AdminRepository(session).get_stats()
    text = (
        "Статистика:\n"
        "\n"
        f"Активных подписок: {stats['active']}\n"
        f"Истекших подписок: {stats['expired']}\n"
        f"Общий доход: {stats['revenue']} руб."
    )
    await callback.message.edit_text(text, reply_markup=_back_menu_keyboard())


def _display_name(user: User) -> str:
    """Human-readable display name for a user."""
    if user.username:
        return f"@{user.username}"
    if user.first_name:
        return user.first_name
    return str(user.telegram_id)


# ---------------------------------------------------------------------------
# Grant subscription flow (FSM-based)
# ---------------------------------------------------------------------------


@admin_router.callback_query(F.data == "adm:grant")
async def grant_start_callback(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Start grant flow: ask admin for user identifier."""
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer()
    await state.set_state(AdminGrant.waiting_for_user)
    await callback.message.edit_text(
        "Введите @username или Telegram ID пользователя:"
    )


@admin_router.message(AdminGrant.waiting_for_user)
async def grant_receive_user(
    message: Message, session: AsyncSession, state: FSMContext
) -> None:
    """Receive user identifier and look up in DB."""
    if not _is_admin(message.from_user.id):
        return

    text = message.text.strip()
    repo = AdminRepository(session)

    if text.startswith("@"):
        user = await repo.find_user_by_username(text)
    else:
        try:
            tid = int(text)
        except ValueError:
            await message.answer(
                "Неверный формат. Введите @username или числовой Telegram ID."
            )
            return
        user = await repo.find_user_by_telegram_id(tid)

    if not user:
        await message.answer(
            "Пользователь не найден. Попробуйте ещё раз или /admin для отмены."
        )
        return

    display = _display_name(user)
    await state.update_data(target_user_id=user.id, target_display=display)
    await state.set_state(AdminGrant.waiting_for_plan)
    await message.answer(
        f"Пользователь: {display}\nВыберите план подписки:",
        reply_markup=grant_plan_keyboard(),
    )


@admin_router.callback_query(F.data.startswith("adm:grant_plan:"))
async def grant_plan_callback(
    callback: CallbackQuery, session: AsyncSession, state: FSMContext
) -> None:
    """Grant selected plan to the target user."""
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer()

    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    target_display = data.get("target_display", "")

    if not target_user_id:
        await callback.message.edit_text(
            "Сессия истекла. Начните заново через /admin.",
            reply_markup=admin_menu_keyboard(),
        )
        await state.clear()
        return

    plan_idx = int(callback.data.split(":")[-1])
    plans = get_settings().plans
    if plan_idx < 0 or plan_idx >= len(plans):
        await callback.message.edit_text(
            "Неверный план.", reply_markup=admin_menu_keyboard()
        )
        await state.clear()
        return

    plan = plans[plan_idx]

    # Activate subscription (price=0 for free grant)
    sub_service = SubscriptionService(session)
    await sub_service.activate(
        user_id=target_user_id,
        plan_name=plan["name"],
        price=0,
        days=plan["days"],
    )

    # Issue invite link and send to user
    repo = AdminRepository(session)
    user = await session.get(User, target_user_id)
    try:
        channel_service = ChannelAccessService(callback.bot, session)
        invite_link = await channel_service.issue_invite(user)
        await channel_service.send_invite_to_user(user, invite_link)
    except Exception as exc:
        logger.warning("Failed to send invite for granted user %s: %s", target_display, exc)

    await state.clear()
    await callback.message.edit_text(
        f"Подписка {plan['name']} выдана пользователю {target_display} "
        f"на {plan['days']} дней.",
        reply_markup=admin_menu_keyboard(),
    )


# ---------------------------------------------------------------------------
# Manage individual subscriber (/manage command)
# ---------------------------------------------------------------------------


@admin_router.message(Command("manage"))
async def manage_cmd(message: Message, session: AsyncSession) -> None:
    """Show subscription management for a specific user.

    Usage: /manage @username  or  /manage 123456789
    """
    if not _is_admin(message.from_user.id):
        return

    args = message.text.strip().split(maxsplit=1)
    if len(args) < 2:
        await message.answer(
            "Использование: /manage @username или /manage telegram_id"
        )
        return

    identifier = args[1].strip()
    repo = AdminRepository(session)

    if identifier.startswith("@"):
        user = await repo.find_user_by_username(identifier)
    else:
        try:
            tid = int(identifier)
        except ValueError:
            await message.answer("Неверный формат идентификатора.")
            return
        user = await repo.find_user_by_telegram_id(tid)

    if not user:
        await message.answer("Пользователь не найден.")
        return

    sub_repo = SubscriptionRepository(session)
    sub = await sub_repo.get_active_for_user(user.id)
    if not sub:
        await message.answer("У пользователя нет активной подписки.")
        return

    display = _display_name(user)
    expires = sub.expires_at.strftime("%d.%m.%Y")
    await message.answer(
        f"Подписчик: {display}\n"
        f"План: {sub.plan_name}\n"
        f"Действует до: {expires}",
        reply_markup=manage_subscription_keyboard(user.id),
    )


# ---------------------------------------------------------------------------
# Extend and revoke handlers
# ---------------------------------------------------------------------------


@admin_router.callback_query(F.data.startswith("adm:extend:"))
async def extend_callback(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Extend a user's subscription by N days."""
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer()

    parts = callback.data.split(":")
    user_db_id = int(parts[2])
    days = int(parts[3])

    sub_repo = SubscriptionRepository(session)
    sub = await sub_repo.get_active_for_user(user_db_id)
    if not sub:
        await callback.message.edit_text(
            "У пользователя нет активной подписки.",
            reply_markup=admin_menu_keyboard(),
        )
        return

    sub_service = SubscriptionService(session)
    await sub_service.extend_subscription(sub, days)

    new_expires = sub.expires_at.strftime("%d.%m.%Y")
    await callback.message.edit_text(
        f"Подписка продлена на {days} дней.\n"
        f"Новая дата окончания: {new_expires}",
        reply_markup=admin_menu_keyboard(),
    )


@admin_router.callback_query(F.data.startswith("adm:revoke:"))
async def revoke_callback(
    callback: CallbackQuery, session: AsyncSession
) -> None:
    """Revoke a user's subscription and kick from channel."""
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer()

    user_db_id = int(callback.data.split(":")[-1])
    user = await session.get(User, user_db_id)
    if not user:
        await callback.message.edit_text(
            "Пользователь не найден.", reply_markup=admin_menu_keyboard()
        )
        return

    sub_repo = SubscriptionRepository(session)
    sub = await sub_repo.get_active_for_user(user.id)
    if not sub:
        await callback.message.edit_text(
            "У пользователя нет активной подписки.",
            reply_markup=admin_menu_keyboard(),
        )
        return

    display = _display_name(user)

    # Expire subscription
    sub_service = SubscriptionService(session)
    await sub_service.expire_subscription(sub)

    # Kick user from channel
    try:
        channel_service = ChannelAccessService(callback.bot, session)
        await channel_service.kick_user(user)
    except Exception as exc:
        logger.warning("Failed to kick user %s: %s", display, exc)

    await callback.message.edit_text(
        f"Подписка пользователя {display} отозвана, "
        "пользователь удалён из канала.",
        reply_markup=admin_menu_keyboard(),
    )
