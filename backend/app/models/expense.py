from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String, UniqueConstraint, text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin, UserOwnedMixin


class Expense(UserOwnedMixin, TimestampMixin, Base):
    __tablename__ = "expenses"
    # Supports "this week / this month" totals per user
    __table_args__ = (
        Index("ix_expenses_user_id_spent_at", "user_id", "spent_at"),
        # A bank SMS read twice must not be recorded twice (NULL for expenses added in chat)
        UniqueConstraint("user_id", "reference"),
    )
    user_id_indexed = False  # covered by the composite index above

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # The bank's transaction reference, for expenses recorded from a bank SMS
    reference: Mapped[str | None] = mapped_column(String(64), nullable=True)
    # False after "Don't count": kept, but left out of totals, the daily budget and the default list
    counted: Mapped[bool] = mapped_column(Boolean, server_default=true(), default=True, nullable=False)
    spent_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
