from datetime import datetime
from typing import ClassVar

from sqlalchemy import DateTime, ForeignKey, Integer, func, text
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), onupdate=func.now(), nullable=False
    )


class UserOwnedMixin:
    """Adds a `user_id` that is deleted along with its user.

    Indexed by default. Set `user_id_indexed = False` when a composite index
    leading with `user_id` already covers it.
    """

    user_id_indexed: ClassVar[bool] = True

    @declared_attr
    def user_id(cls) -> Mapped[int]:  # noqa: N805
        return mapped_column(
            Integer,
            ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=cls.user_id_indexed,
        )
