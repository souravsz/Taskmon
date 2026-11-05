"""Operations paused until the user gives missing info, picks a record, or confirms. Stored in MySQL.

`state` (JSON) is the operation being built:
    {"intent", "data": {field: raw value}, "target": {...}, "target_ids": [..] | None,
     "confirmed": bool, "duplicate_ok": bool, "queue": [other operations waiting their turn]}
"""

from datetime import timedelta
from typing import Any

from sqlalchemy import select

from app.ai.intent_catalogue import INTENTS
from app.ai.schemas import Selection
from app.conversation.context import Turn, utcnow
from app.core.config import settings
from app.models import PendingAction, PendingStatus
from app.models.pending_action import WAITING_STATUSES

KIND = {
    PendingStatus.WAITING_FOR_INFO: "info",
    PendingStatus.WAITING_FOR_TARGET_SELECTION: "select",
    PendingStatus.WAITING_FOR_CONFIRMATION: "confirm",
}


def get_active(turn: Turn) -> tuple[PendingAction | None, dict[str, Any] | None]:
    """(the open pending action, or None; what just expired, if anything)."""
    pending = turn.db.scalar(
        select(PendingAction)
        .where(
            PendingAction.conversation_id == turn.conversation.id,
            PendingAction.user_id == turn.user.id,
            PendingAction.status.in_(WAITING_STATUSES),
        )
        .order_by(PendingAction.id.desc())
        .limit(1)
    )
    if pending is None:
        turn.step("pending.none")
        return None, None
    if pending.expires_at < utcnow():
        close(turn, pending, PendingStatus.EXPIRED)
        return None, {"intent": pending.intent, "question": pending.question}
    turn.step(
        "pending.loaded",
        id=pending.id,
        intent=pending.intent,
        status=pending.status.value,
        state=pending.state,
    )
    return pending, None


def to_context(pending: PendingAction | None) -> dict[str, Any] | None:
    """What Groq sees: the intent, what is collected so far, the question asked and the choices offered."""
    if pending is None:
        return None
    state = pending.state
    return {
        "intent": pending.intent,
        "waiting_for": KIND[pending.status],
        "collected": state.get("data", {}),
        "target": state.get("target", {}),
        "missing_fields": state.get("missing_fields", []),
        "question": pending.question,
        "candidates": [
            {"position": c["position"], "title": c["title"], "subtitle": c["subtitle"]}
            for c in pending.candidates or []
        ],
    }


def open_pending(
    turn: Turn,
    state: dict[str, Any],
    status: PendingStatus,
    question: str,
    candidates: list[dict[str, Any]] | None = None,
) -> None:
    """Ask the user something and remember the operation. Only one question per reply: if one is already
    being asked, this operation waits in the queue and is asked about afterwards."""
    if turn.new_pending is not None:
        turn.deferred.append(state)
        turn.step("pending.deferred", intent=state["intent"], reason="another question is already open")
        return

    for old in turn.db.scalars(
        select(PendingAction).where(
            PendingAction.conversation_id == turn.conversation.id, PendingAction.status.in_(WAITING_STATUSES)
        )
    ):
        close(turn, old, PendingStatus.CANCELLED, reason="replaced by a new question")

    pending = PendingAction(
        user_id=turn.user.id,
        conversation_id=turn.conversation.id,
        intent=state["intent"],
        status=status,
        state=state,
        question=question,
        expires_at=utcnow() + timedelta(minutes=settings.PENDING_ACTION_MINUTES),
    )
    turn.db.add(pending)
    turn.new_pending = pending
    if candidates:
        turn.say(question, records=candidates, title=INTENTS[state["intent"]].module.capitalize())
        pending.candidates = turn.shown  # numbered, so "2" or "the second one" can be matched
    else:
        turn.say(question)
    turn.db.flush()
    turn.step("pending.opened", id=pending.id, status=status.value, question=question, state=state)


def close(turn: Turn, pending: PendingAction, status: PendingStatus, reason: str | None = None) -> None:
    pending.status = status
    pending.resolved_at = utcnow()
    turn.db.flush()
    turn.step("pending.closed", id=pending.id, status=status.value, reason=reason)


def match_candidate(pending: PendingAction, selection: Selection) -> dict[str, Any] | None:
    """The candidate the user picked, by number or by title words."""
    candidates = pending.candidates or []
    if selection.position and 1 <= selection.position <= len(candidates):
        return candidates[selection.position - 1]
    if selection.text:
        words = selection.text.lower().split()
        matches = [c for c in candidates if all(w in f"{c['title']} {c['subtitle']}".lower() for w in words)]
        if len(matches) == 1:
            return matches[0]
    return None
