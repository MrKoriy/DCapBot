from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.payment import Payment
from bot.models.subscription import Subscription
from bot.models.user import User


class AdminRepository:
    """Data-access layer for admin panel queries."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_subscribers_page(
        self, page: int, per_page: int = 10
    ) -> tuple[list[tuple[User, Subscription]], int]:
        """Return paginated active subscribers and total count.

        Subscribers are ordered by soonest-expiring first.
        """
        base_filter = Subscription.status == "active"

        # Total count of active subscriptions
        count_result = await self._session.execute(
            select(func.count()).select_from(Subscription).where(base_filter)
        )
        total = count_result.scalar_one()

        # Paginated list of (User, Subscription) tuples
        result = await self._session.execute(
            select(User, Subscription)
            .join(Subscription, Subscription.user_id == User.id)
            .where(base_filter)
            .order_by(Subscription.expires_at.asc())
            .offset(page * per_page)
            .limit(per_page)
        )
        rows = [(row[0], row[1]) for row in result.all()]

        return rows, total

    async def get_stats(self) -> dict[str, int]:
        """Return aggregate statistics: active/expired subscription counts and revenue."""
        active_result = await self._session.execute(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.status == "active")
        )
        active = active_result.scalar_one()

        expired_result = await self._session.execute(
            select(func.count())
            .select_from(Subscription)
            .where(Subscription.status == "expired")
        )
        expired = expired_result.scalar_one()

        revenue_result = await self._session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == "succeeded"
            )
        )
        revenue = revenue_result.scalar_one()

        return {"active": active, "expired": expired, "revenue": revenue}

    async def find_user_by_telegram_id(self, telegram_id: int) -> User | None:
        """Find a user by their Telegram ID."""
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_first()

    async def find_user_by_username(self, username: str) -> User | None:
        """Find a user by username (case-insensitive, strips leading @)."""
        username = username.lstrip("@")
        result = await self._session.execute(
            select(User).where(func.lower(User.username) == username.lower())
        )
        return result.scalar_first()
