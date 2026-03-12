from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.payment import Payment


class PaymentRepository:
    """Data-access layer for Payment records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_pending(
        self,
        user_id: int,
        payment_id: str,
        amount: int,
        currency: str,
        plan_name: str,
    ) -> Payment:
        """Create a new Payment with status='pending' and flush (no commit)."""
        payment = Payment(
            user_id=user_id,
            payment_id=payment_id,
            amount=amount,
            currency=currency,
            status="pending",
            plan_name=plan_name,
        )
        self._session.add(payment)
        await self._session.flush()
        return payment

    async def find_by_payment_id(self, payment_id: str) -> Payment | None:
        """Look up a payment by its YooKassa UUID."""
        result = await self._session.execute(
            select(Payment).where(Payment.payment_id == payment_id)
        )
        return result.scalar_one_or_none()

    async def mark_succeeded(self, payment_id: str) -> Payment | None:
        """Mark payment as succeeded. Returns None if not found."""
        payment = await self.find_by_payment_id(payment_id)
        if payment is None:
            return None
        payment.status = "succeeded"
        payment.confirmed_at = datetime.utcnow()
        await self._session.flush()
        return payment
