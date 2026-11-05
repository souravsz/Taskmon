from decimal import Decimal

from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # E.164 format, e.g. +919876543210 (max 15 digits plus '+')
    mobile_number: Mapped[str] = mapped_column(String(16), unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(30), unique=True, nullable=True)
    # Spending limit in INR; NULL means no limit set
    expense_limit: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    # IANA name; chat dates ("tomorrow 8 PM") are read and stored in this zone
    timezone: Mapped[str] = mapped_column(
        String(64), server_default="Asia/Kolkata", default="Asia/Kolkata", nullable=False
    )

    def __repr__(self) -> str:
        return f"<User id={self.id}>"
