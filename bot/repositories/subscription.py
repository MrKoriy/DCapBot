from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from bot.models.subscription import Subscription
from bot.models.user import User


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

    async def get_expired_active(self) -> list[Subscription]:
        """Find all active subscriptions that have expired."""
        now = datetime.utcnow()
        result = await self._session.execute(
            select(Subscription)
            .options(selectinload(Subscription.user))
            .where(
                Subscription.status == "active",
                Subscription.expires_at < now,
            )
        )
        return list(result.scalars().all())

    async def get_expiring_soon(self, days: int = 3) -> list[Subscription]:
        """Find active subscriptions expiring within `days` days that haven't been reminded."""
        now = datetime.utcnow()
        cutoff = now + timedelta(days=days)
        result = await self._session.execute(
            select(Subscription)
            .options(selectinload(Subscription.user))
            .where(
                Subscription.status == "active",
                Subscription.expires_at >= now,
                Subscription.expires_at <= cutoff,
                Subscription.reminder_sent == False,  # noqa: E712
            )
        )
        return list(result.scalars().all())

    async def get_all_active_user_ids(self) -> list[int]:
        """Return telegram_ids for all users with at least one active subscription."""
        result = await self._session.execute(
            select(User.telegram_id)
            .join(Subscription, Subscription.user_id == User.id)
            .where(Subscription.status == "active")
            .distinct()
        )
        return list(result.scalars().all())

    async def get_users_without_active_sub(self) -> list[User]:
        """Find users not banned who have no active subscription (ghost members)."""
        active_sub_exists = (
            select(Subscription.id)
            .where(
                Subscription.user_id == User.id,
                Subscription.status == "active",
            )
            .exists()
        )
        result = await self._session.execute(
            select(User).where(
                User.channel_banned == False,  # noqa: E712
                ~active_sub_exists,
            )
        )
        return list(result.scalars().all())
