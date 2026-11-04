from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, false
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin, UserOwnedMixin


class NotificationTask(UserOwnedMixin, TimestampMixin, Base):
    """A reminder to notify the user at `notify_at`, optionally linked to a task."""

    __tablename__ = "notification_tasks"
    # A scheduler polls: WHERE is_notified = 0 AND notify_at <= now()
    __table_args__ = (Index("ix_notification_tasks_is_notified_notify_at", "is_notified", "notify_at"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    notify_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_notified: Mapped[bool] = mapped_column(Boolean, server_default=false(), default=False, nullable=False)
    notified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_completed: Mapped[bool] = mapped_column(Boolean, server_default=false(), default=False, nullable=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, server_default=false(), default=False, nullable=False)
    # NULL for one-off reminders; otherwise daily | weekdays | weekly | monthly
    recurrence: Mapped[str | None] = mapped_column(String(20), nullable=True)
