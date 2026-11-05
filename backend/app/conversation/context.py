"""What the engine knows while handling one message, and the CONTEXT it sends to Groq."""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import ActionHistory, Conversation, Message, MessageRole, PendingAction, User, UserDetail

logger = logging.getLogger("app.chat")

HISTORY_MESSAGES = 6  # recent messages sent to Groq
HISTORY_CHARS = 600  # each one trimmed to this length
MEMORIES = 10


def utcnow() -> datetime:
    """Naive UTC, used for bookkeeping timestamps (pending expiry, action history)."""
    return datetime.now(UTC).replace(tzinfo=None)


def local_now(user: User) -> datetime:
    """The user's wall-clock time, naive. Reminders and expenses are stored in this time."""
    try:
        zone = ZoneInfo(user.timezone or settings.DEFAULT_TIMEZONE)
    except ZoneInfoNotFoundError:
        zone = ZoneInfo(settings.DEFAULT_TIMEZONE)
    return datetime.now(zone).replace(tzinfo=None, second=0, microsecond=0)


@dataclass
class Turn:
    """State for one incoming message: who, where, and the reply being built."""

    db: Session
    user: User
    conversation: Conversation
    now: datetime
    last_shown: list[dict[str, Any]] = field(default_factory=list)  # records the user last saw, with ids
    last_action: ActionHistory | None = None
    parts: list[dict[str, Any]] = field(default_factory=list)  # reply parts: {"text", "card"}
    shown: list[dict[str, Any]] = field(default_factory=list)  # records shown in this reply (numbered)
    new_pending: PendingAction | None = None  # the question this reply asks, if any
    deferred: list[dict[str, Any]] = field(
        default_factory=list
    )  # operations that must wait for that question
    trace: list[dict[str, Any]] = field(default_factory=list)

    def step(self, name: str, **details: Any) -> None:
        """Debug trace: logged, and returned to the frontend when CHAT_DEBUG is on."""
        self.trace.append({"step": name, **details})
        logger.log(
            logging.INFO if settings.CHAT_DEBUG else logging.DEBUG,
            "chat user=%s conv=%s %s %s",
            self.user.id,
            self.conversation.id,
            name,
            details or "",
        )

    def say(
        self,
        text: str,
        records: list[dict[str, Any]] | None = None,
        title: str | None = None,
        summary: str | None = None,
        numbered: bool = True,
    ) -> None:
        """Add a reply part. Numbered records become CONTEXT.last_shown_records ("the second one")."""
        card = None
        if records is not None:
            rows = [{**r, "position": i if numbered else None} for i, r in enumerate(records, 1)]
            card = {"title": title or "", "summary": summary, "records": rows}
            if numbered and rows:
                self.shown = rows
        self.parts.append({"text": text, "card": card})


def recent_history(db: Session, conversation: Conversation) -> list[dict[str, str]]:
    rows = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id, Message.role != MessageRole.SYSTEM)
        .order_by(Message.id.desc())
        .limit(HISTORY_MESSAGES)
    ).all()
    return [{"role": m.role.value, "content": m.content[:HISTORY_CHARS]} for m in reversed(rows)]


def last_shown_records(db: Session, conversation: Conversation) -> list[dict[str, Any]]:
    """Numbered records from the most recent reply that showed any (within the recent messages)."""
    payloads = db.scalars(
        select(Message.payload)
        .where(Message.conversation_id == conversation.id, Message.role == MessageRole.ASSISTANT)
        .order_by(Message.id.desc())
        .limit(HISTORY_MESSAGES)
    ).all()
    for payload in payloads:
        if payload and payload.get("shown"):
            return list(payload["shown"])
    return []


def last_action(db: Session, user: User, conversation: Conversation) -> ActionHistory | None:
    return db.scalar(
        select(ActionHistory)
        .where(
            ActionHistory.user_id == user.id,
            ActionHistory.conversation_id == conversation.id,
            ActionHistory.undone_at.is_(None),
        )
        .order_by(ActionHistory.id.desc())
        .limit(1)
    )


def user_memories(db: Session, user: User) -> list[str]:
    rows = db.scalars(
        select(UserDetail.content)
        .where(UserDetail.user_id == user.id)
        .order_by(UserDetail.id.desc())
        .limit(MEMORIES)
    ).all()
    return list(rows)


def _without_ids(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Groq sees positions and titles, never database ids."""
    return [{k: v for k, v in r.items() if k not in ("id", "detail")} for r in records]


SUMMARY_FIELDS = ("title", "description", "amount", "category", "notify_at", "spent_at", "recurrence")


def action_summary(action: ActionHistory | None) -> dict[str, Any] | None:
    """{"intent", "records": [{title, amount, ...}]} for CONTEXT.last_action."""
    if action is None:
        return None
    snapshots = action.after or action.before or []
    records = [{k: s[k] for k in SUMMARY_FIELDS if s.get(k) is not None} for s in snapshots]
    return {"intent": action.intent, "records": records}


def build_context(
    turn: Turn, pending: dict[str, Any] | None, expired: dict[str, Any] | None
) -> dict[str, Any]:
    """Pending action, relevant application data and long-term preferences (history is sent separately)."""
    context: dict[str, Any] = {
        "now": turn.now.strftime("%Y-%m-%d %H:%M (%A)"),
        "timezone": turn.user.timezone,
        "pending_action": pending,
        "last_shown_records": _without_ids(turn.last_shown),
        "last_action": action_summary(turn.last_action),
        "user_memories": user_memories(turn.db, turn.user),
    }
    if expired:
        context["expired_pending_action"] = expired
    return context
