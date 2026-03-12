from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from bot.models.base import Base

if TYPE_CHECKING:
    from bot.models.user import User


class Payment(Base):
    __tablename__ = "payments"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), index=True, nullable=False
    )
    payment_id: Mapped[str] = mapped_column(unique=True, nullable=False)
    amount: Mapped[int] = mapped_column(nullable=False)
    currency: Mapped[str] = mapped_column(default="RUB", server_default="RUB")
    status: Mapped[str] = mapped_column(default="pending", server_default="pending")
    plan_name: Mapped[str] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    confirmed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped[User] = relationship(back_populates="payments")
