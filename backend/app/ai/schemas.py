"""The JSON Groq must return. Every reply is validated against `ClassifierResult` before
FastAPI acts on it."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

MessageType = Literal["ACTION", "QUERY", "CLARIFICATION", "CONVERSATION", "FALLBACK"]
PendingReply = Literal["none", "answer", "select", "confirm", "deny", "cancel"]


class _Lenient(BaseModel):
    model_config = ConfigDict(extra="ignore")


class Target(_Lenient):
    """Which existing record(s) an operation applies to. Groq never sends ids."""

    text: str | None = None  # words from the title / description / category
    date: str | None = None  # YYYY-MM-DD
    time: str | None = None  # HH:MM, reminders only ("my 8 PM reminder")
    position: int | None = None  # 1-based index into last_shown_records
    ref: str | None = None  # "last_action" | "latest"
    all: bool = False

    def is_empty(self) -> bool:
        return not (self.text or self.date or self.time or self.position or self.ref or self.all)


class Operation(_Lenient):
    intent: str
    data: dict[str, Any] = Field(default_factory=dict)
    target: Target = Field(default_factory=Target)
    missing_fields: list[str] = Field(default_factory=list)

    @field_validator("data", mode="before")
    @classmethod
    def _drop_empty_values(cls, v: Any) -> Any:
        # Groq often sends {"date": null}; null means "not given"
        return {k: val for k, val in v.items() if val not in (None, "")} if isinstance(v, dict) else v

    @field_validator("target", mode="before")
    @classmethod
    def _null_target(cls, v: Any) -> Any:
        return v or {}


class Selection(_Lenient):
    position: int | None = None
    text: str | None = None


class ClassifierResult(_Lenient):
    type: MessageType
    pending: PendingReply = "none"
    operations: list[Operation] = Field(default_factory=list)
    selection: Selection = Field(default_factory=Selection)
    response: str | None = None

    @field_validator("type", mode="before")
    @classmethod
    def _upper(cls, v: Any) -> Any:
        return v.strip().upper() if isinstance(v, str) else v

    @field_validator("pending", mode="before")
    @classmethod
    def _lower(cls, v: Any) -> Any:
        return v.strip().lower() if isinstance(v, str) else (v or "none")

    @field_validator("operations", "selection", mode="before")
    @classmethod
    def _null_to_default(cls, v: Any, info: Any) -> Any:
        if v is None:
            return [] if info.field_name == "operations" else {}
        return v
