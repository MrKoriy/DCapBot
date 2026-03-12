from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base

if TYPE_CHECKING:
    from bot.models.payment import Payment
    from bot.models.subscription import Subscription


class User(Base):
    __tablename__ = "users"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    username: Mapped[str | None] = mapped_column(nullable=True)
    first_name: Mapped[str | None] = mapped_column(nullable=True)
    channel_banned: Mapped[bool] = mapped_column(default=False, server_default="false")

    subscriptions: Mapped[list[Subscription]] = relationship(
        back_populates="user", lazy="selectin"
    )
    payments: Mapped[list[Payment]] = relationship(
        back_populates="user", lazy="selectin"
    )
