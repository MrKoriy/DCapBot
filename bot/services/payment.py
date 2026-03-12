from __future__ import annotations

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from yookassa import Configuration
from yookassa import Payment as YkPayment

from bot.config import get_settings
from bot.models.user import User
from bot.repositories.payment import PaymentRepository

logger = logging.getLogger(__name__)


class PaymentService:
    """Orchestrates YooKassa payment creation and persistence."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = PaymentRepository(session)

    async def create_payment(self, user: User, plan_index: int, bot_username: str) -> str:
        """Create a YooKassa payment, persist pending record, return payment URL.

        The YooKassa SDK is synchronous, so the API call is wrapped in
        ``asyncio.to_thread`` to avoid blocking the event loop.
        """
        settings = get_settings()
        plan = settings.plans[plan_index]

        # Configure YooKassa credentials
        Configuration.account_id = settings.yookassa_shop_id
        Configuration.secret_key = settings.yookassa_secret_key

        params = {
            "amount": {
                "value": f"{plan['price']}.00",
                "currency": "RUB",
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"https://t.me/{bot_username}",
            },
            "capture": True,
            "description": f"Подписка: {plan['name']}",
            "receipt": {
                "customer": {
                    "email": "subscriber@example.com",
                },
                "items": [
                    {
                        "description": f"Подписка на канал: {plan['name']}",
                        "quantity": "1.00",
                        "amount": {
                            "value": f"{plan['price']}.00",
                            "currency": "RUB",
                        },
                        "vat_code": 1,
                        "payment_subject": "service",
                        "payment_mode": "full_payment",
                    }
                ],
            },
            "metadata": {
                "telegram_id": str(user.telegram_id),
                "user_id": str(user.id),
                "plan_index": str(plan_index),
            },
        }

        # Non-blocking YooKassa SDK call
        yk_payment = await asyncio.to_thread(YkPayment.create, params)

        # Persist pending payment record
        await self._repo.create_pending(
            user_id=user.id,
            payment_id=yk_payment.id,
            amount=plan["price"],
            currency="RUB",
            plan_name=plan["name"],
        )
        await self._session.commit()

        return yk_payment.confirmation.confirmation_url
