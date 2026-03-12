from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    """Admin panel main menu: subscribers and statistics."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Подписчики", callback_data="adm:subscribers")
    builder.button(text="Статистика", callback_data="adm:stats")
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
