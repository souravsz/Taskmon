from typing import Any, Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    conversation_id: int | None = None  # omit to start a new conversation
    # Unique per message (e.g. a UUID). A retry with the same id gets the stored reply instead of running twice.
    client_message_id: str | None = Field(default=None, min_length=1, max_length=64)
    # A quick-action button (Today / Reminders / Expenses / Notes): runs the list directly, no Groq call
    # "expenses_all": the Show all button, which adds the "Don't count" expenses
    quick_action: Literal["today", "reminders", "expenses", "expenses_all", "notes"] | None = None


class ChatRecord(BaseModel):
    position: int | None  # number shown to the user ("cancel the second one"); None for summary rows
    entity: str  # reminder | expense | note | category | month
    id: int
    title: str
    subtitle: str
    detail: str | None = None  # a note's full text, when asked for
    counted: bool | None = None  # expenses only: False after "Don't count"; the app shows a toggle button


class ChatCard(BaseModel):
    title: str
    summary: str | None
    records: list[ChatRecord]
    # An expense list that left out "Don't count" expenses: the app shows a Show all button
    show_all: bool = False


class ChatPart(BaseModel):
    text: str
    card: ChatCard | None = None


class ChatPending(BaseModel):
    """The question this reply is waiting on. `confirm` → show Yes / No."""

    kind: Literal["info", "select", "confirm"]
    question: str


class ChatResponse(BaseModel):
    conversation_id: int
    message_id: int
    type: str  # ACTION | QUERY | CLARIFICATION | CONVERSATION | FALLBACK
    text: str  # all parts' text, one per line
    parts: list[ChatPart]
    pending: ChatPending | None = None
    debug: list[dict[str, Any]] | None = None  # every engine step, only when CHAT_DEBUG=true
