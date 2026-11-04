import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin, UserOwnedMixin


class PendingStatus(enum.StrEnum):
    WAITING_FOR_INFO = "WAITING_FOR_INFO"
    WAITING_FOR_TARGET_SELECTION = "WAITING_FOR_TARGET_SELECTION"
    WAITING_FOR_CONFIRMATION = "WAITING_FOR_CONFIRMATION"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


WAITING_STATUSES = (
    PendingStatus.WAITING_FOR_INFO,
    PendingStatus.WAITING_FOR_TARGET_SELECTION,
    PendingStatus.WAITING_FOR_CONFIRMATION,
)


class PendingAction(UserOwnedMixin, TimestampMixin, Base):
    """An operation paused until the user supplies info, picks a record, or confirms."""

    __tablename__ = "pending_actions"
    __table_args__ = (Index("ix_pending_actions_conversation_id_status", "conversation_id", "status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    intent: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[PendingStatus] = mapped_column(
        Enum(PendingStatus, name="pending_status", values_callable=lambda e: [m.value for m in e]),
        nullable=False,
    )
    # Serialised OperationState: collected fields, target criteria, resolved target ids, flags
    state: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    # Records offered for selection: [{"position", "entity", "id", "title", "subtitle"}]
    candidates: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    question: Mapped[str | None] = mapped_column(Text, nullable=True)
    # The assistant message that asked `question`; a "yes" only counts if it answers this message
    prompt_message_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("messages.id", ondelete="SET NULL"), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
