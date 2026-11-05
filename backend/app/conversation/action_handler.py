"""Runs one operation: validate fields → ask for anything missing → find the target record(s) →
confirm if needed → call the service → write action history. Also undo."""

import calendar
import hashlib
import json
import re
from datetime import date, datetime, time, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy import DateTime, Numeric, select

from app.ai.intent_catalogue import CATEGORIES, INTENTS, QUERY, QUESTIONS, RECURRENCES, Intent
from app.ai.response_generator import Record, day_label, describe, inr, record_card, when
from app.ai.schemas import Operation, Target
from app.conversation.context import Turn, utcnow
from app.conversation.pending_actions import open_pending
from app.conversation.query_handler import run_query
from app.models import ActionHistory, Expense, Note, NotificationTask, PendingStatus
from app.services import expense_service, note_service, reminder_service

ENTITY = {"reminders": "reminder", "expenses": "expense", "notes": "note"}
MODELS: dict[str, type[Record]] = {"reminder": NotificationTask, "expense": Expense, "note": Note}
DUPLICATE_WINDOW = timedelta(minutes=10)
MAX_AMOUNT = Decimal("10000000")  # ₹1 crore per expense
CANDIDATES = 10


class Invalid(Exception):  # noqa: N818  (it's a reply, not an error)
    """A value the user must give again. `fields` are cleared and `message` is asked."""

    def __init__(self, fields: tuple[str, ...], message: str) -> None:
        super().__init__(message)
        self.fields = fields
        self.message = message


def new_state(op: Operation) -> dict[str, Any]:
    """Operation from Groq → the state stored while it is in progress (see pending_actions)."""
    return {
        "intent": op.intent,
        "data": dict(op.data),
        "target": op.target.model_dump(),
        "target_ids": None,
        "missing_fields": [],
        "confirmed": False,
    }


# ---------------------------------------------------------------- field validation


def parse_date(raw: Any, field: str = "date") -> date:
    text = str(raw).strip()
    try:
        return date.fromisoformat(text)
    except ValueError:
        m = re.fullmatch(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
        if m and 1 <= int(m[2]) <= 12:
            raise Invalid(
                (field,),
                f"{calendar.month_name[int(m[2])]} {int(m[3])} isn't a valid date. Which date did you mean?",
            ) from None
        raise Invalid((field,), f"I couldn't read the date “{text}”. Which date did you mean?") from None


def parse_time(raw: Any) -> time:
    text = str(raw).strip()
    m = re.fullmatch(r"(\d{1,2}):(\d{2})(?::\d{2})?", text)
    if not m or int(m[1]) > 23 or int(m[2]) > 59:
        raise Invalid(("time",), f"I couldn't read the time “{text}”. What time should it be?")
    return time(int(m[1]), int(m[2]))


def parse_month(raw: Any, field: str) -> date:
    m = re.fullmatch(r"(\d{4})-(\d{1,2})", str(raw).strip())
    if not m or not 1 <= int(m[2]) <= 12:
        raise Invalid((field,), f"I couldn't read the month “{raw}”. Which month did you mean?")
    return date(int(m[1]), int(m[2]), 1)


def parse_amount(raw: Any) -> Decimal:
    text = str(raw).replace("₹", "").replace(",", "").replace("Rs", "").strip()
    try:
        amount = Decimal(text).quantize(Decimal("0.01"))
    except InvalidOperation:
        raise Invalid(("amount",), f"I couldn't read the amount “{raw}”. How much was it?") from None
    if amount <= 0 or amount >= MAX_AMOUNT:
        raise Invalid(("amount",), "The amount should be more than ₹0. How much was it?")
    return amount


def validate(intent: Intent, data: dict[str, Any]) -> dict[str, Any]:
    """Raw values from Groq → typed values. Fields the intent doesn't use are ignored."""
    values: dict[str, Any] = {}
    for f in intent.fields:
        if f not in data:
            continue
        raw = data[f]
        if f in ("title", "description", "content", "append", "text"):
            text = str(raw).strip()
            if text and f in ("title", "description"):
                values[f] = (text[0].upper() + text[1:])[:255]
            elif text:
                values[f] = text
        elif f in ("date", "date_from", "date_to"):
            values[f] = parse_date(raw, f)
        elif f == "time":
            values[f] = parse_time(raw)
        elif f in ("month", "compare_month"):
            values[f] = parse_month(raw, f)
        elif f == "amount":
            values[f] = parse_amount(raw)
        elif f == "category":
            values[f] = next((c for c in CATEGORIES if c.lower() == str(raw).strip().lower()), "Misc")
        elif f == "recurrence":
            rec = str(raw).strip().lower()
            if rec not in RECURRENCES:
                raise Invalid((f,), QUESTIONS["recurrence"])
            values[f] = rec
        elif f == "module":
            module = str(raw).strip().lower()
            if module in ENTITY:
                values[f] = module
    return values


# ---------------------------------------------------------------- the operation


async def run_operation(turn: Turn, state: dict[str, Any]) -> None:
    intent = INTENTS[state["intent"]]
    turn.step("operation.start", intent=intent.id, data=state["data"], target=state["target"])
    try:
        values = validate(intent, state["data"])
        missing = [f for f in intent.required if f not in values]
        if missing:
            state["missing_fields"] = missing
            turn.step("operation.missing", fields=missing)
            open_pending(
                turn,
                state,
                PendingStatus.WAITING_FOR_INFO,
                QUESTIONS.get(missing[0], f"What's the {missing[0]}?"),
            )
            return
        state["missing_fields"] = []
        turn.step("operation.validated", values={k: str(v) for k, v in values.items()})

        if intent.kind == QUERY:
            await run_query(turn, intent, values)
            return
        if intent.id == "undo_last_action":
            undo(turn, values.get("module"))
            return

        records: list[Any] = []
        if intent.needs_target:
            found = resolve_target(turn, intent, state)
            if found is None:
                return
            records = found
            turn.step("target.resolved", ids=[r.id for r in records])

        if intent.module == "reminders":
            run_reminder(turn, intent, values, records, state)
        elif intent.module == "expenses":
            run_expense(turn, intent, values, records, state)
        else:
            run_note(turn, intent, values, records, state)
    except Invalid as exc:
        for f in exc.fields:
            state["data"].pop(f, None)
        state["confirmed"] = False
        turn.step("operation.invalid", fields=exc.fields, message=exc.message)
        open_pending(turn, state, PendingStatus.WAITING_FOR_INFO, exc.message)


# ---------------------------------------------------------------- finding the records an operation targets


def load_owned(turn: Turn, entity: str, ids: list[int]) -> list[Any]:
    """Only the current user's records: ids from anywhere else are simply not found."""
    model = MODELS[entity]
    rows = turn.db.scalars(select(model).where(model.id.in_(ids), model.user_id == turn.user.id)).all()
    by_id = {r.id: r for r in rows}
    return [by_id[i] for i in ids if i in by_id]


def find_records(turn: Turn, intent: Intent, target: Target) -> list[Any]:
    entity = ENTITY[intent.module]
    day = parse_date(target.date) if target.date else None
    at = parse_time(target.time) if target.time else None
    uid = turn.user.id
    if entity == "reminder":
        return reminder_service.find(
            turn.db, uid, target.text, day, at, include_closed=intent.id == "delete_reminder"
        )
    if entity == "expense":
        return expense_service.find(turn.db, uid, target.text, day)
    return (
        note_service.search(turn.db, uid, target.text)
        if target.text
        else note_service.list_recent(turn.db, uid)[0]
    )


def all_records(turn: Turn, entity: str) -> list[Any]:
    model = MODELS[entity]
    return list(turn.db.scalars(select(model).where(model.user_id == turn.user.id).order_by(model.id)))


def latest_record(turn: Turn, entity: str) -> Any:
    service = {"reminder": reminder_service, "expense": expense_service, "note": note_service}[entity]
    return service.latest(turn.db, turn.user.id)


def criteria_text(target: Target, now: datetime) -> str:
    parts = []
    if target.text:
        parts.append(f"“{target.text}”")
    if target.date:
        try:
            parts.append(f"on {day_label(date.fromisoformat(target.date), now.date())}")
        except ValueError:
            parts.append(f"on {target.date}")
    if target.time:
        parts.append(f"at {target.time}")
    return " ".join(parts)


def resolve_target(turn: Turn, intent: Intent, state: dict[str, Any]) -> list[Any] | None:
    """The record(s) to act on, or None after telling the user (not found) or asking them (pick one)."""
    entity = ENTITY[intent.module]
    if state.get("target_ids"):
        rows = load_owned(turn, entity, state["target_ids"])
        if not rows:
            turn.say(f"That {entity} doesn't exist any more.")
        return rows or None

    target = Target(**state["target"])
    if target.all and intent.destructive:
        rows = all_records(turn, entity)
        if not rows:
            turn.say(f"You don't have any {entity}s.")
            return None
        state["target_ids"] = [r.id for r in rows]
        return rows

    if target.ref == "last_action" and turn.last_action and turn.last_action.module == intent.module:
        rows = load_owned(turn, entity, turn.last_action.record_ids)
        turn.step("target.last_action", history_id=turn.last_action.id, ids=[r.id for r in rows])
        if len(rows) == 1:
            return rows
    elif target.ref == "latest":
        row = latest_record(turn, entity)
        if row is None:
            turn.say(f"You don't have any {entity}s yet.")
            return None
        return [row]

    if target.position:
        shown = turn.last_shown
        picked = shown[target.position - 1] if 1 <= target.position <= len(shown) else None
        turn.step("target.position", position=target.position, picked=picked)
        words = (target.text or "").lower().split()
        if picked and words and not all(w in picked["title"].lower() for w in words):
            # Groq sent words AND a number that don't agree (e.g. a stale list): trust the words
            turn.step("target.position_ignored", reason="title doesn't match target.text")
            target.position = None
    if target.position:
        if picked is None or picked["entity"] != entity:
            turn.say(f"I can't find a {entity} number {target.position} in the last list I showed you.")
            return None
        rows = load_owned(turn, entity, [picked["id"]])
        if not rows:
            turn.say(f"That {entity} doesn't exist any more.")
            return None
        return rows

    has_criteria = bool(target.text or target.date or target.time)
    rows = find_records(turn, intent, target)
    turn.step("target.search", criteria=target.model_dump(), found=len(rows))
    if not rows:
        what = criteria_text(target, turn.now)
        turn.say(
            f"I couldn't find a {entity} matching {what}."
            if has_criteria
            else f"You don't have any {entity}s yet."
        )
        return None
    if len(rows) == 1 and has_criteria:
        return rows

    question = (
        f"I found {len(rows)} {entity}s matching {criteria_text(target, turn.now)}. Which one do you mean?"
        if has_criteria
        else f"Which {entity} do you mean?"
    )
    open_pending(
        turn,
        state,
        PendingStatus.WAITING_FOR_TARGET_SELECTION,
        question,
        candidates=[record_card(r, turn.now) for r in rows[:CANDIDATES]],
    )
    return None


# ---------------------------------------------------------------- confirmation, duplicates, history


def ask_to_confirm(turn: Turn, state: dict[str, Any], question: str) -> bool:
    """True if the user still has to say yes (the question has been asked)."""
    if state.get("confirmed"):
        return False
    open_pending(turn, state, PendingStatus.WAITING_FOR_CONFIRMATION, question)
    return True


def fingerprint(intent_id: str, **fields: Any) -> str:
    payload = json.dumps({"intent": intent_id, **fields}, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()


def is_duplicate(turn: Turn, fp: str) -> bool:
    """Same create in the last few minutes, not undone, and the record still exists."""
    entry = turn.db.scalar(
        select(ActionHistory)
        .where(
            ActionHistory.user_id == turn.user.id,
            ActionHistory.fingerprint == fp,
            ActionHistory.undone_at.is_(None),
            ActionHistory.created_at >= utcnow() - DUPLICATE_WINDOW,
        )
        .order_by(ActionHistory.id.desc())
        .limit(1)
    )
    if entry is None:
        return False
    still_there = load_owned(turn, ENTITY[entry.module], entry.record_ids)
    turn.step("duplicate.check", history_id=entry.id, still_there=bool(still_there))
    return bool(still_there)


def snapshot(record: Any) -> dict[str, Any]:
    """Column values as JSON (timestamps managed by the database are left out)."""
    snap: dict[str, Any] = {}
    for col in record.__table__.columns:
        if col.name in ("created_at", "updated_at"):
            continue
        value = getattr(record, col.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = str(value.quantize(Decimal("0.01")))
        snap[col.name] = value
    return snap


def from_snapshot(model: type[Record], snap: dict[str, Any]) -> dict[str, Any]:
    values = {}
    for name, value in snap.items():
        col_type = model.__table__.c[name].type
        if value is not None and isinstance(col_type, DateTime):
            value = datetime.fromisoformat(value)
        elif value is not None and isinstance(col_type, Numeric):
            value = Decimal(value)
        values[name] = value
    return values


def record_history(
    turn: Turn,
    intent: Intent,
    operation: str,
    records: list[Any],
    before: list[dict[str, Any]] | None,
    fp: str | None = None,
) -> None:
    after = None if operation == "delete" else [snapshot(r) for r in records]
    entry = ActionHistory(
        user_id=turn.user.id,
        conversation_id=turn.conversation.id,
        intent=intent.id,
        module=intent.module,
        operation=operation,
        record_ids=[r.id for r in records] if records else [s["id"] for s in before or []],
        before=before,
        after=after,
        fingerprint=fp,
        is_reversible=True,
        created_at=utcnow(),
    )
    turn.db.add(entry)
    turn.db.flush()
    turn.step("history.saved", id=entry.id, operation=operation, record_ids=entry.record_ids)


def confirm_delete_question(entity: str, records: list[Any], everything: bool, now: datetime) -> str:
    if everything:
        n = len(records)
        return (
            f"Are you sure you want to delete all your {entity}s ({n} {entity if n == 1 else entity + 's'})?"
        )
    if len(records) == 1:
        return f"Are you sure you want to delete the {entity} {describe(records[0], now)}?"
    return f"Are you sure you want to delete these {len(records)} {entity}s?"


def delete_records(
    turn: Turn, intent: Intent, records: list[Any], state: dict[str, Any], service: Any
) -> None:
    entity = ENTITY[intent.module]
    everything = bool(state["target"].get("all"))
    if ask_to_confirm(turn, state, confirm_delete_question(entity, records, everything, turn.now)):
        return
    before = [snapshot(r) for r in records]
    text = (
        f"Deleted the {entity} {describe(records[0], turn.now)}."
        if len(records) == 1
        else f"Deleted {len(records)} {entity}s."
    )
    for r in records:
        service.delete(turn.db, r)
    record_history(turn, intent, "delete", [], before)
    turn.say(text)


# ---------------------------------------------------------------- reminders


def add_period(at: datetime, recurrence: str) -> datetime:
    if recurrence in ("daily", "weekdays"):
        return at + timedelta(days=1)
    if recurrence == "weekly":
        return at + timedelta(days=7)
    year, month = (at.year + 1, 1) if at.month == 12 else (at.year, at.month + 1)
    return at.replace(year=year, month=month, day=min(at.day, calendar.monthrange(year, month)[1]))


def reminder_time(values: dict[str, Any], now: datetime, current: datetime | None = None) -> datetime:
    """Date + time for a one-off reminder. Without a date: today, or tomorrow if that time has passed."""
    day = values.get("date") or (current.date() if current else now.date())
    at = values.get("time") or (current.time() if current else time(9, 0))
    notify_at = datetime.combine(day, at)
    if notify_at <= now:
        if "date" not in values and current is None:
            return notify_at + timedelta(days=1)
        raise Invalid(
            ("date", "time"), f"{when(notify_at, now)} has already passed. When should I remind you?"
        )
    return notify_at


def first_occurrence(values: dict[str, Any], now: datetime) -> datetime:
    recurrence = values["recurrence"]
    at = datetime.combine(values.get("date") or now.date(), values["time"])
    while at <= now or (recurrence == "weekdays" and at.weekday() >= 5):
        at = add_period(at, recurrence)
    return at


def run_reminder(
    turn: Turn, intent: Intent, values: dict[str, Any], records: list[Any], state: dict[str, Any]
) -> None:
    db, now = turn.db, turn.now
    if intent.id in ("create_reminder", "create_recurring_reminder"):
        recurring = intent.id == "create_recurring_reminder"
        notify_at = first_occurrence(values, now) if recurring else reminder_time(values, now)
        recurrence = values["recurrence"] if recurring else None
        fp = fingerprint(intent.id, title=values["title"].lower(), notify_at=notify_at, recurrence=recurrence)
        if is_duplicate(turn, fp) and ask_to_confirm(
            turn,
            state,
            f"You already added “{values['title']}” for {when(notify_at, now)} a moment ago. Add it again?",
        ):
            return
        reminder = reminder_service.create(db, turn.user.id, values["title"], notify_at, recurrence)
        record_history(turn, intent, "create", [reminder], None, fp)
        turn.say("Reminder set.", records=[record_card(reminder, now)], title="Reminder")
        return

    reminder = records[0]
    before = [snapshot(reminder)]
    if intent.id == "update_reminder":
        if not {"title", "date", "time"} & values.keys():
            open_pending(
                turn,
                {**state, "target_ids": [reminder.id]},
                PendingStatus.WAITING_FOR_INFO,
                "What should I change it to?",
            )
            return
        notify_at = (
            reminder_time(values, now, reminder.notify_at) if {"date", "time"} & values.keys() else None
        )
        reminder_service.update(db, reminder, values.get("title"), notify_at)
        record_history(turn, intent, "update", [reminder], before)
        turn.say("Reminder updated.", records=[record_card(reminder, now)], title="Reminder")
    elif intent.id == "complete_reminder":
        if reminder.is_completed:
            turn.say(f"{describe(reminder, now)} is already marked as done.")
            return
        text = f"Marked {describe(reminder, now)} as done."
        reminder_service.complete(db, reminder)
        record_history(turn, intent, "complete", [reminder], before)
        turn.say(text)
    elif intent.id == "cancel_reminder":
        if reminder.is_cancelled:
            turn.say(f"{describe(reminder, now)} is already cancelled.")
            return
        reminder_service.cancel(db, reminder)
        record_history(turn, intent, "cancel", [reminder], before)
        turn.say(f"Cancelled. I won't remind you about “{reminder.title}”; it stays in your history.")
    elif intent.id == "delete_reminder":
        delete_records(turn, intent, records, state, reminder_service)


# ---------------------------------------------------------------- expenses


def spent_at(values: dict[str, Any], now: datetime, current: datetime | None = None) -> datetime:
    day = values.get("date") or (current.date() if current else now.date())
    if day > now.date():
        raise Invalid(("date",), "That date is in the future. When did you spend it?")
    if current is not None:
        return datetime.combine(day, current.time())
    return now if day == now.date() else datetime.combine(day, time(12, 0))


def run_expense(
    turn: Turn, intent: Intent, values: dict[str, Any], records: list[Any], state: dict[str, Any]
) -> None:
    db, now = turn.db, turn.now
    if intent.id == "create_expense":
        when_spent = spent_at(values, now)
        category = values.get("category", "Misc")
        description = values.get("description")
        fp = fingerprint(
            intent.id,
            amount=values["amount"],
            category=category,
            description=(description or "").lower(),
            day=when_spent.date(),
        )
        if is_duplicate(turn, fp) and ask_to_confirm(
            turn,
            state,
            f"You already added {describe_amount(values['amount'], category)} a moment ago. Add it again?",
        ):
            return
        expense = expense_service.create(
            db, turn.user.id, values["amount"], category, description, when_spent
        )
        record_history(turn, intent, "create", [expense], None, fp)
        turn.say("Expense added.", records=[record_card(expense, now)], title="Expense")
        return

    if intent.id == "delete_expense":
        delete_records(turn, intent, records, state, expense_service)
        return

    expense = records[0]  # update_expense
    if not {"amount", "category", "description", "date"} & values.keys():
        open_pending(
            turn,
            {**state, "target_ids": [expense.id]},
            PendingStatus.WAITING_FOR_INFO,
            "What should I change it to?",
        )
        return
    before = [snapshot(expense)]
    new_spent_at = spent_at(values, now, expense.spent_at) if "date" in values else None
    expense_service.update(
        db, expense, values.get("amount"), values.get("category"), values.get("description"), new_spent_at
    )
    record_history(turn, intent, "update", [expense], before)
    turn.say("Expense updated.", records=[record_card(expense, now)], title="Expense")


def describe_amount(amount: Decimal, category: str) -> str:
    return f"{inr(amount)} for {category}"


# ---------------------------------------------------------------- notes


def run_note(
    turn: Turn, intent: Intent, values: dict[str, Any], records: list[Any], state: dict[str, Any]
) -> None:
    db, now = turn.db, turn.now
    if intent.id == "create_note":
        fp = fingerprint(intent.id, title=values["title"].lower(), content=values.get("content"))
        if is_duplicate(turn, fp) and ask_to_confirm(
            turn, state, f"You just saved “{values['title']}”. Save it again?"
        ):
            return
        note = note_service.create(db, turn.user.id, values["title"], values.get("content"))
        record_history(turn, intent, "create", [note], None, fp)
        turn.say("Note saved.", records=[record_card(note, now, full=True)], title="Note")
        return

    if intent.id == "delete_note":
        delete_records(turn, intent, records, state, note_service)
        return

    note = records[0]  # update_note
    if not {"title", "content", "append"} & values.keys():
        open_pending(
            turn,
            {**state, "target_ids": [note.id]},
            PendingStatus.WAITING_FOR_INFO,
            "What should I add or change?",
        )
        return
    before = [snapshot(note)]
    note_service.update(db, note, values.get("title"), values.get("content"), values.get("append"))
    record_history(turn, intent, "update", [note], before)
    turn.say("Note updated.", records=[record_card(note, now, full=True)], title="Note")


# ---------------------------------------------------------------- undo

UNDONE = {
    "create": "removed",
    "delete": "brought back",
    "update": "changed back",
    "complete": "reopened",
    "cancel": "re-activated",
}


def undo(turn: Turn, module: str | None) -> None:
    """Reverse the latest change (optionally of one module), only if the record is still as we left it."""
    query = select(ActionHistory).where(
        ActionHistory.user_id == turn.user.id, ActionHistory.undone_at.is_(None)
    )
    if module:
        query = query.where(ActionHistory.module == module)
    entry = turn.db.scalar(query.order_by(ActionHistory.id.desc()).limit(1))
    turn.step("undo.entry", id=entry.id if entry else None, module=module)
    what = f"{ENTITY[module]} change" if module else "change"
    if entry is None:
        turn.say(f"There's no recent {what} to undo.")
        return
    if not entry.is_reversible:
        turn.say("I can't safely undo that one.")
        return

    entity = ENTITY[entry.module]
    model = MODELS[entity]
    current = load_owned(turn, entity, entry.record_ids)

    if entry.operation == "delete":
        if current:
            turn.say(f"I can't undo that: the {entity} already exists again.")
            return
        restored = []
        for snap in entry.before or []:
            record = model(**from_snapshot(model, snap))
            turn.db.add(record)
            restored.append(record)
        turn.db.flush()
    else:
        if len(current) != len(entry.record_ids) or [snapshot(r) for r in current] != (entry.after or []):
            turn.say(f"That {entity} has changed since, so I won't undo it automatically.")
            return
        restored = current
        if entry.operation == "create":
            for r in current:
                turn.db.delete(r)
        else:
            for r, snap in zip(current, entry.before or [], strict=True):
                for name, value in from_snapshot(model, snap).items():
                    setattr(r, name, value)
        turn.db.flush()

    entry.undone_at = utcnow()
    turn.db.flush()
    turn.step("undo.done", id=entry.id, operation=entry.operation)
    names = ", ".join(f"“{record_card(r, turn.now)['title']}”" for r in restored)
    shown = [] if entry.operation == "create" else [record_card(r, turn.now) for r in restored]
    turn.say(
        f"Undone: {UNDONE.get(entry.operation, 'reversed')} the {entity} {names}.",
        records=shown or None,
        title=entity.capitalize(),
    )
