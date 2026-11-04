from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin, UserOwnedMixin


class UserDetail(UserOwnedMixin, TimestampMixin, Base):
    """Free-form paragraphs about a user (preferences, context, facts to remember)."""

    __tablename__ = "user_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
