from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.subscription import Subscription


class SubscriptionRepository:
    """Data-access layer for Subscription records."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: int,
        plan_name: str,
        price: int,
        starts_at: datetime,
        expires_at: datetime,
    ) -> Subscription:
        """Create a new active Subscription and flush (no commit)."""
        sub = Subscription(
            user_id=user_id,
            plan_name=plan_name,
            price=price,
            status="active",
            starts_at=starts_at,
            expires_at=expires_at,
            reminder_sent=False,
        )
        self._session.add(sub)
        await self._session.flush()
        return sub

    async def get_active_for_user(self, user_id: int) -> Subscription | None:
        """Find the most recent active subscription for a user."""
        result = await self._session.execute(
            select(Subscription)
            .where(
                Subscription.user_id == user_id,
                Subscription.status == "active",
            )
            .order_by(Subscription.expires_at.desc())
        )
        return result.scalar_first()
