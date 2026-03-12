from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.subscription import Subscription
from bot.repositories.subscription import SubscriptionRepository


class SubscriptionService:
    """Orchestrates subscription activation."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = SubscriptionRepository(session)
        self._session = session

    async def activate(
        self,
        user_id: int,
        plan_name: str,
        price: int,
        days: int,
    ) -> Subscription:
        """Create an active subscription starting now, expiring in `days` days."""
        starts_at = datetime.utcnow()
        expires_at = starts_at + timedelta(days=days)
        return await self._repo.create(
            user_id=user_id,
            plan_name=plan_name,
            price=price,
            starts_at=starts_at,
            expires_at=expires_at,
        )

    async def expire_subscription(self, subscription: Subscription) -> None:
        """Mark a subscription as expired."""
        subscription.status = "expired"
        await self._session.flush()
