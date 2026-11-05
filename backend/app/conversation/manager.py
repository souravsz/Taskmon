"""The conversation engine: one entry point for every chat message.

load conversation + pending action → build context → Groq classifies → route:
  reply to a pending question  → continue that operation
  ACTION / QUERY               → run each operation
  CONVERSATION / CLARIFICATION → Groq's reply
  FALLBACK (unrelated, or Groq's reply unusable twice) → one fixed reply
→ save both messages → commit → structured reply
"""

import copy
import logging
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.ai.intent_catalogue import INTENTS
from app.ai.intent_classifier import classify
from app.ai.schemas import ClassifierResult, Operation, Selection
from app.conversation import conversation_handler, pending_actions
from app.conversation.action_handler import new_state, run_operation
from app.conversation.context import (
    Turn,
    build_context,
    last_action,
    last_shown_records,
    local_now,
    recent_history,
)
from app.core.config import settings
from app.core.exceptions import AIServiceError, ConflictError, DatabaseError, NotFoundError
from app.models import Conversation, Message, MessageRole, PendingAction, PendingStatus, User
from app.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger("app.chat")


async def handle_message(db: Session, user: User, body: ChatRequest) -> ChatResponse:
    if body.client_message_id and (replay := find_replay(db, user, body.client_message_id)):
        logger.info("chat user=%s replaying reply for client_message_id=%s", user.id, body.client_message_id)
        return replay

    conversation = get_or_create_conversation(db, user, body)
    turn = Turn(db=db, user=user, conversation=conversation, now=local_now(user))
    turn.step("received", message=body.message, client_message_id=body.client_message_id, now=str(turn.now))

    # Context: pending action, records last shown, last change, preferences, recent messages
    pending, expired = pending_actions.get_active(turn)
    turn.last_shown = last_shown_records(db, conversation)
    turn.last_action = last_action(db, user, conversation)
    history = recent_history(db, conversation)
    context = build_context(turn, pending_actions.to_context(pending), expired)
    turn.step("context", context=context, history=history)
    last_prompt_id = db.scalar(
        select(Message.id)
        .where(Message.conversation_id == conversation.id, Message.role == MessageRole.ASSISTANT)
        .order_by(Message.id.desc())
        .limit(1)
    )

    db.add(
        Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=body.message,
            client_message_id=body.client_message_id,
        )
    )
    try:
        db.flush()
    except IntegrityError:  # the same client_message_id arrived twice at once
        db.rollback()
        if body.client_message_id and (replay := find_replay(db, user, body.client_message_id)):
            return replay
        raise ConflictError("This message is already being processed.") from None

    if body.quick_action:
        result = quick_action_result(body.quick_action, turn)
        turn.step("quick_action", action=body.quick_action, groq_called=False)
    else:
        calls: list[dict[str, Any]] = []
        try:
            result = await classify(context, history, body.message, calls)
        except AIServiceError as exc:
            db.rollback()  # nothing is saved, so the user can simply send it again
            logger.warning(
                "chat user=%s conv=%s groq failed: %s | calls=%s",
                user.id,
                conversation.id,
                exc.message,
                calls,
            )
            raise
        turn.groq_steps(calls, "classify")
    turn.step("classified", result=result.model_dump())

    try:
        await route(turn, result, pending, expired, last_prompt_id)
        attach_deferred(turn)
        response = save_reply(turn, result)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("chat user=%s conv=%s database error, turn rolled back", user.id, conversation.id)
        raise DatabaseError() from exc
    return response


# ---------------------------------------------------------------- quick actions

# Buttons under the chat box always mean the same thing, so they skip Groq
QUICK_ACTIONS = {
    "today": "list_reminders",
    "reminders": "list_reminders",
    "expenses": "list_expenses",
    "notes": "list_notes",
}


def quick_action_result(action: str, turn: Turn) -> ClassifierResult:
    today = turn.now.date().isoformat()
    data = {"date_from": today, "date_to": today} if action == "today" else {}
    return ClassifierResult(type="QUERY", operations=[Operation(intent=QUICK_ACTIONS[action], data=data)])


# ---------------------------------------------------------------- routing


async def route(
    turn: Turn,
    result: ClassifierResult,
    pending: PendingAction | None,
    expired: dict[str, Any] | None,
    last_prompt_id: int | None,
) -> None:
    if pending is not None and result.pending != "none":
        turn.step("route.pending_reply", reply=result.pending, pending_id=pending.id)
        await continue_pending(turn, pending, result, last_prompt_id)
        # anything else asked in the same message ("yes, and add ₹50 for coffee"). Groq often repeats the
        # pending operation itself next to a pick or a yes; running that again would ask the same question.
        ops = result.operations[1:] if result.pending == "answer" else result.operations
        extra = [op for op in ops if result.pending == "answer" or op.intent != pending.intent]
        if len(extra) < len(ops):
            turn.step("pending.echo_ignored", intent=pending.intent)
        for op in extra:
            await run_operation(turn, new_state(op))
        return

    if pending is None and expired and result.pending in ("answer", "select", "confirm"):
        turn.step("route.expired_reply", expired=expired)
        turn.say("Sorry, that earlier request timed out. Could you tell me again in full?")
        return

    if result.type in ("ACTION", "QUERY") and result.operations:
        turn.step("route.operations", count=len(result.operations), pending_kept=pending is not None)
        for op in result.operations:
            await run_operation(turn, new_state(op))
        return

    turn.step("route.conversation", type=result.type, pending_kept=pending is not None)
    conversation_handler.reply(turn, result)


def reask(turn: Turn, pending: PendingAction, prefix: str = "") -> None:
    """Ask the open question again (it stays open and now points at this reply)."""
    turn.step("pending.reask", id=pending.id, prefix=prefix)
    if pending.candidates:
        records = [{k: v for k, v in c.items() if k != "position"} for c in pending.candidates]
        turn.say(
            prefix + (pending.question or ""),
            records=records,
            title=INTENTS[pending.intent].module.capitalize(),
        )
    else:
        turn.say(prefix + (pending.question or ""))
    turn.new_pending = pending


async def continue_pending(
    turn: Turn, pending: PendingAction, result: ClassifierResult, last_prompt_id: int | None
) -> None:
    """The user answered, picked, confirmed, refused or cancelled the open question."""
    state = copy.deepcopy(pending.state)
    queue = state.pop("queue", [])
    reply = result.pending

    if reply in ("cancel", "deny"):
        is_confirm = pending.status == PendingStatus.WAITING_FOR_CONFIRMATION
        pending_actions.close(turn, pending, PendingStatus.CANCELLED, reason=reply)
        turn.say("Okay, I won't do that." if reply == "deny" and is_confirm else "Okay, I've cancelled that.")

    elif reply == "confirm":
        if pending.status != PendingStatus.WAITING_FOR_CONFIRMATION:
            reask(turn, pending)
            return
        # A "yes" only counts if it answers the latest question we asked
        if pending.prompt_message_id != last_prompt_id:
            reask(turn, pending, prefix="Just to be sure: ")
            return
        state["confirmed"] = True
        pending_actions.close(turn, pending, PendingStatus.COMPLETED, reason="confirmed")
        await run_operation(turn, state)

    elif reply == "select":
        selection = result.selection
        # Groq sometimes leaves "selection" empty and puts the pick in a repeated operation's target instead
        echoed = next((op for op in result.operations if op.intent == pending.intent), None)
        if not (selection.position or selection.text) and echoed:
            selection = Selection(position=echoed.target.position, text=echoed.target.text)
        picked = pending_actions.match_candidate(pending, selection)
        turn.step("pending.select", selection=selection.model_dump(), picked=picked)
        if pending.status != PendingStatus.WAITING_FOR_TARGET_SELECTION or picked is None:
            reask(turn, pending, prefix="I didn't catch which one. " if picked is None else "")
            return
        state["target_ids"] = [picked["id"]]
        pending_actions.close(turn, pending, PendingStatus.COMPLETED, reason="selected")
        await run_operation(turn, state)

    else:  # answer
        op = result.operations[0] if result.operations else None
        if op is None:
            reask(turn, pending)
            return
        state["data"].update(op.data)
        if not op.target.is_empty():
            state["target"] = op.target.model_dump()
            state["target_ids"] = None
        state["confirmed"] = False
        turn.step("pending.answer", merged_data=state["data"], target=state["target"])
        pending_actions.close(turn, pending, PendingStatus.COMPLETED, reason="answered")
        await run_operation(turn, state)

    for queued in queue:  # operations that were waiting for this question to be settled
        turn.step("queue.run", intent=queued["intent"])
        await run_operation(turn, queued)


def attach_deferred(turn: Turn) -> None:
    """Operations that also need a question wait in the open pending action's queue."""
    if not turn.deferred or turn.new_pending is None:
        return
    pending = turn.new_pending
    pending.state = {**pending.state, "queue": [*pending.state.get("queue", []), *turn.deferred]}
    turn.db.flush()
    turn.step("queue.saved", pending_id=pending.id, intents=[s["intent"] for s in turn.deferred])
    turn.say("I'll come back to the rest once that's sorted.")


# ---------------------------------------------------------------- persistence


def get_or_create_conversation(db: Session, user: User, body: ChatRequest) -> Conversation:
    if body.conversation_id is not None:
        conversation = db.get(Conversation, body.conversation_id)
        if conversation is None or conversation.user_id != user.id:
            raise NotFoundError("Conversation not found")
        return conversation
    conversation = Conversation(user_id=user.id, title=body.message[:60])
    db.add(conversation)
    db.flush()
    return conversation


def save_reply(turn: Turn, result: ClassifierResult) -> ChatResponse:
    parts = turn.parts or [{"text": "Done.", "card": None}]
    text = "\n".join(p["text"] for p in parts)
    pending = turn.new_pending
    reply = {
        "type": result.type,
        "text": text,
        "parts": parts,
        "pending": {"kind": pending_actions.KIND[pending.status], "question": pending.question}
        if pending
        else None,
    }
    message = Message(
        conversation_id=turn.conversation.id,
        role=MessageRole.ASSISTANT,
        content=text,
        payload=jsonable_encoder({"reply": reply, "shown": turn.shown}),
    )
    turn.db.add(message)
    turn.db.flush()
    if pending is not None:
        pending.prompt_message_id = message.id  # a later "yes" must answer exactly this message
        turn.db.flush()
    turn.step("reply.saved", message_id=message.id, pending_id=pending.id if pending else None, text=text)
    return ChatResponse(
        conversation_id=turn.conversation.id,
        message_id=message.id,
        **reply,
        debug=jsonable_encoder(turn.trace) if settings.CHAT_DEBUG else None,
    )


def find_replay(db: Session, user: User, client_message_id: str) -> ChatResponse | None:
    """The stored reply to a message we already handled (a retry after a dropped connection)."""
    asked = db.scalar(
        select(Message)
        .join(Conversation, Conversation.id == Message.conversation_id)
        .where(
            Conversation.user_id == user.id,
            Message.client_message_id == client_message_id,
            Message.role == MessageRole.USER,
        )
    )
    if asked is None:
        return None
    answer = db.scalar(
        select(Message)
        .where(
            Message.conversation_id == asked.conversation_id,
            Message.role == MessageRole.ASSISTANT,
            Message.id > asked.id,
        )
        .order_by(Message.id)
        .limit(1)
    )
    if answer is None or not answer.payload:
        return None
    return ChatResponse(
        conversation_id=asked.conversation_id, message_id=answer.id, **answer.payload["reply"]
    )
