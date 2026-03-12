from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from bot.config import get_settings


def plan_selection_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard with subscription plan buttons."""
    builder = InlineKeyboardBuilder()
    plans = get_settings().plans

    for idx, plan in enumerate(plans):
        builder.button(
            text=f"{plan['name']} \u2014 {plan['price']} \u20bd",
            callback_data=f"plan:{idx}",
        )

    builder.adjust(1)
    return builder.as_markup()
