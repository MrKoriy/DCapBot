from __future__ import annotations

import math

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import get_settings
from bot.keyboards.admin import admin_menu_keyboard, subscribers_pagination_keyboard
from bot.models.user import User
from bot.repositories.admin import AdminRepository

admin_router = Router()

PER_PAGE = 10


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
