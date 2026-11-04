from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import UserOwnedMixin


class ActionHistory(UserOwnedMixin, Base):
    """Audit trail of executed operations, with before/after snapshots for undo."""

    __tablename__ = "action_history"
    __table_args__ = (Index("ix_action_history_user_id_created_at", "user_id", "created_at"),)
    user_id_indexed = False  # covered by the composite index above

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True
    )
    intent: Mapped[str] = mapped_column(String(64), nullable=False)
    module: Mapped[str] = mapped_column(String(32), nullable=False)
    operation: Mapped[str] = mapped_column(String(32), nullable=False)
    record_ids: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    before: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    after: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)
    # Normalised input, used to spot accidental duplicate creates
    fingerprint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_reversible: Mapped[bool] = mapped_column(Boolean, nullable=False)
    undone_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=text("CURRENT_TIMESTAMP"), nullable=False
    )
