from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import get_settings


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Admin panel main menu: subscribers, statistics, and grant."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Подписчики", callback_data="adm:subscribers")
    builder.button(text="Статистика", callback_data="adm:stats")
    builder.button(text="Выдать подписку", callback_data="adm:grant")
    builder.adjust(1)
    return builder.as_markup()


def grant_plan_keyboard() -> InlineKeyboardMarkup:
    """Plan selection keyboard for granting a free subscription."""
    builder = InlineKeyboardBuilder()
    plans = get_settings().plans
    for idx, plan in enumerate(plans):
        builder.button(
            text=f"{plan['name']} — {plan['days']} дней",
            callback_data=f"adm:grant_plan:{idx}",
        )
    builder.button(text="Отмена", callback_data="adm:menu")
    builder.adjust(1)
    return builder.as_markup()


def manage_subscription_keyboard(user_db_id: int) -> InlineKeyboardMarkup:
    """Subscription management keyboard: extend or revoke."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text="Продлить на 7 дней", callback_data=f"adm:extend:{user_db_id}:7"
    )
    builder.button(
        text="Продлить на 30 дней", callback_data=f"adm:extend:{user_db_id}:30"
    )
    builder.button(
        text="Отозвать подписку", callback_data=f"adm:revoke:{user_db_id}"
    )
    builder.button(text="Назад в меню", callback_data="adm:menu")
    builder.adjust(1)
    return builder.as_markup()


def subscribers_pagination_keyboard(
    page: int, total_pages: int
) -> InlineKeyboardMarkup:
    """Pagination controls for the subscriber list."""
    builder = InlineKeyboardBuilder()

    if total_pages > 1:
        if page > 0:
            builder.button(text="<<", callback_data=f"adm:subs:{page - 1}")
        if page < total_pages - 1:
            builder.button(text=">>", callback_data=f"adm:subs:{page + 1}")

    builder.button(text="Назад в меню", callback_data="adm:menu")

    # Navigation buttons in one row, back button on its own row
    if total_pages > 1:
        nav_count = (1 if page > 0 else 0) + (1 if page < total_pages - 1 else 0)
        builder.adjust(nav_count, 1)
    else:
        builder.adjust(1)

    return builder.as_markup()
