"""Chat engine scenarios. Groq is replaced by a scripted fake: each test says what Groq would return,
and checks what FastAPI does with it (validation, context, pending actions, database changes)."""

import asyncio
import json
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

import groq
import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import groq_client, intent_classifier, response_generator
from app.core.config import settings
from app.models import (
    ActionHistory,
    Expense,
    Message,
    Note,
    NotificationTask,
    PendingAction,
    PendingStatus,
    User,
)
from tests.conftest import API, auth_header, login


def today() -> date:
    return datetime.now(ZoneInfo("Asia/Kolkata")).date()


TOMORROW = (today() + timedelta(days=1)).isoformat()
YESTERDAY = (today() - timedelta(days=1)).isoformat()


class FakeGroq:
    def __init__(self) -> None:
        self.replies: list[Any] = []
        self.calls: list[list[dict[str, str]]] = []

    async def __call__(
        self, messages: list[dict[str, str]], json_mode: bool = True, calls: list[dict] | None = None
    ) -> str:
        self.calls.append(messages)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        text = reply if isinstance(reply, str) else json.dumps(reply)
        if calls is not None:
            calls.append(
                {"request": {"model": "fake", "messages": messages}, "response": text, "duration_ms": 1}
            )
        return text

    def context(self, call: int = -1) -> dict[str, Any]:
        """The CONTEXT block sent to Groq in a call."""
        return json.loads(self.calls[call][1]["content"].removeprefix("CONTEXT: "))


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> FakeGroq:
    fake = FakeGroq()
    monkeypatch.setattr(intent_classifier, "chat_completion", fake)
    monkeypatch.setattr(response_generator, "chat_completion", fake)
    monkeypatch.setattr(settings, "GROQ_API_KEY", SecretStr("test-key"))
    monkeypatch.setattr(settings, "CHAT_DEBUG", True)
    return fake


def op(intent: str, data: dict | None = None, **target: Any) -> dict[str, Any]:
    return {"intent": intent, "data": data or {}, "target": target, "missing_fields": []}


def result(
    type_: str, *ops: dict, pending: str = "none", selection: dict | None = None, response: str | None = None
) -> dict:
    return {
        "type": type_,
        "pending": pending,
        "operations": list(ops),
        "selection": selection or {},
        "response": response,
    }


class Chat:
    """One user in one conversation."""

    def __init__(self, client: TestClient, fake: FakeGroq, mobile: str = "9876543210") -> None:
        self.client, self.fake = client, fake
        self.token = login(client, mobile)["access_token"]
        self.conversation_id: int | None = None

    def send(self, message: str, *groq_replies: Any, client_message_id: str | None = None) -> dict[str, Any]:
        self.fake.replies.extend(groq_replies)
        body = {
            "message": message,
            "conversation_id": self.conversation_id,
            "client_message_id": client_message_id,
        }
        res = self.client.post(f"{API}/chat", json=body, headers=auth_header(self.token))
        assert res.status_code == 200, res.text
        data = res.json()
        self.conversation_id = data["conversation_id"]
        return data


@pytest.fixture
def chat(client: TestClient, fake: FakeGroq) -> Chat:
    return Chat(client, fake)


def rows(db: Session, model: Any) -> list[Any]:
    db.expire_all()
    return list(db.scalars(select(model).order_by(model.id)))


def user_id(db: Session) -> int:
    return db.scalars(select(User.id)).first()  # type: ignore[return-value]


def add_reminder(db: Session, title: str, at: datetime) -> NotificationTask:
    r = NotificationTask(user_id=user_id(db), title=title, notify_at=at)
    db.add(r)
    db.commit()
    return r


def add_expense(
    db: Session, amount: str, category: str, description: str | None, spent_at: datetime
) -> Expense:
    e = Expense(
        user_id=user_id(db),
        amount=Decimal(amount),
        category=category,
        description=description,
        spent_at=spent_at,
    )
    db.add(e)
    db.commit()
    return e


def add_note(db: Session, title: str, content: str | None = None) -> Note:
    n = Note(user_id=user_id(db), title=title, content=content)
    db.add(n)
    db.commit()
    return n


def at(day: str | date, hh: int, mm: int = 0) -> datetime:
    d = date.fromisoformat(day) if isinstance(day, str) else day
    return datetime.combine(d, time(hh, mm))


# ======================================================================== reminders


def test_create_reminder(chat: Chat, db_session: Session) -> None:
    reply = chat.send(
        "Remind me to call Rahul tomorrow at 8 PM",
        result("ACTION", op("create_reminder", {"title": "Call Rahul", "date": TOMORROW, "time": "20:00"})),
    )
    [r] = rows(db_session, NotificationTask)
    assert (r.title, r.notify_at) == ("Call Rahul", at(TOMORROW, 20))
    assert reply["type"] == "ACTION" and reply["pending"] is None
    assert reply["parts"][0]["text"] == "Reminder set."
    assert reply["parts"][0]["card"]["records"][0]["subtitle"] == "Tomorrow · 8:00 PM"
    assert [h.operation for h in rows(db_session, ActionHistory)] == ["create"]


def test_missing_time_is_asked_then_continued(chat: Chat, db_session: Session) -> None:
    reply = chat.send(
        "Remind me to call Rahul",
        result("ACTION", op("create_reminder", {"title": "Call Rahul"})),
    )
    assert reply["pending"] == {"kind": "info", "question": "When should I remind you?"}
    assert rows(db_session, NotificationTask) == []

    reply = chat.send(
        "Tomorrow at 8 PM",
        result("ACTION", op("create_reminder", {"date": TOMORROW, "time": "20:00"}), pending="answer"),
    )
    # Groq was told about the pending reminder, with what had been collected so far
    pending_ctx = chat.fake.context()["pending_action"]
    assert pending_ctx["intent"] == "create_reminder"
    assert pending_ctx["collected"] == {"title": "Call Rahul"}
    assert pending_ctx["missing_fields"] == ["time"]

    [r] = rows(db_session, NotificationTask)
    assert (r.title, r.notify_at) == ("Call Rahul", at(TOMORROW, 20))
    assert reply["pending"] is None
    assert [p.status for p in rows(db_session, PendingAction)] == [PendingStatus.COMPLETED]


def test_update_reminder(chat: Chat, db_session: Session) -> None:
    add_reminder(db_session, "Call Rahul", at(TOMORROW, 20))
    chat.send(
        "Change Rahul's reminder to 9 PM",
        result("ACTION", op("update_reminder", {"time": "21:00"}, text="Rahul")),
    )
    [r] = rows(db_session, NotificationTask)
    assert r.notify_at == at(TOMORROW, 21)


def test_multiple_matches_ask_to_pick_one(chat: Chat, db_session: Session) -> None:
    add_reminder(db_session, "Team meeting", at(TOMORROW, 10))
    add_reminder(db_session, "Client meeting", at(TOMORROW, 15))

    reply = chat.send("Cancel my meeting reminder", result("ACTION", op("cancel_reminder", text="meeting")))
    assert reply["pending"]["kind"] == "select"
    card = reply["parts"][0]["card"]
    assert [(r["position"], r["title"]) for r in card["records"]] == [
        (1, "Team meeting"),
        (2, "Client meeting"),
    ]
    assert chat.fake.context()["pending_action"] is None

    chat.send("The second one", result("ACTION", pending="select", selection={"position": 2}))
    assert chat.fake.context()["pending_action"]["candidates"][1]["title"] == "Client meeting"
    team, client = rows(db_session, NotificationTask)
    assert (team.is_cancelled, client.is_cancelled) == (False, True)


def test_not_found(chat: Chat, db_session: Session) -> None:
    add_reminder(db_session, "Team meeting", at(TOMORROW, 10))
    reply = chat.send("Cancel my gym reminder", result("ACTION", op("cancel_reminder", text="gym")))
    assert reply["text"] == "I couldn't find a reminder matching “gym”."
    assert reply["pending"] is None


def test_complete_reminder(chat: Chat, db_session: Session) -> None:
    add_reminder(db_session, "Call Rahul", at(TOMORROW, 20))
    chat.send("Mark my call reminder as completed", result("ACTION", op("complete_reminder", text="call")))
    [r] = rows(db_session, NotificationTask)
    assert r.is_completed and not r.is_cancelled


def test_cancel_by_time_keeps_the_record(chat: Chat, db_session: Session) -> None:
    add_reminder(db_session, "Call Rahul", at(TOMORROW, 20))
    add_reminder(db_session, "Gym", at(TOMORROW, 7))
    reply = chat.send("Cancel my 8 PM reminder", result("ACTION", op("cancel_reminder", time="20:00")))
    call, gym = rows(db_session, NotificationTask)
    assert call.is_cancelled and not gym.is_cancelled
    assert "Cancelled" in reply["text"]


def test_delete_reminder_needs_confirmation(chat: Chat, db_session: Session) -> None:
    add_reminder(db_session, "Dentist", at(TOMORROW, 16))
    reply = chat.send("Delete my dentist reminder", result("ACTION", op("delete_reminder", text="dentist")))
    assert reply["pending"]["kind"] == "confirm"
    assert len(rows(db_session, NotificationTask)) == 1

    chat.send("Yes", result("ACTION", pending="confirm"))
    assert rows(db_session, NotificationTask) == []


def test_delete_denied(chat: Chat, db_session: Session) -> None:
    add_reminder(db_session, "Dentist", at(TOMORROW, 16))
    chat.send("Delete my dentist reminder", result("ACTION", op("delete_reminder", text="dentist")))
    reply = chat.send("No", result("ACTION", pending="deny"))
    assert reply["text"] == "Okay, I won't do that."
    assert len(rows(db_session, NotificationTask)) == 1


def test_recurring_reminder(chat: Chat, db_session: Session) -> None:
    chat.send(
        "Remind me to exercise every morning",
        result(
            "ACTION",
            op("create_recurring_reminder", {"title": "Exercise", "time": "08:00", "recurrence": "daily"}),
        ),
    )
    [r] = rows(db_session, NotificationTask)
    assert r.recurrence == "daily" and r.notify_at.time() == time(8, 0)
    assert r.notify_at > datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)


# ======================================================================== expenses


def test_create_expense(chat: Chat, db_session: Session) -> None:
    chat.send(
        "I spent ₹350 on food today",
        result("ACTION", op("create_expense", {"amount": 350, "category": "food", "description": "Food"})),
    )
    [e] = rows(db_session, Expense)
    assert (e.amount, e.category, e.spent_at.date()) == (Decimal("350.00"), "Food", today())


def test_update_yesterdays_expense(chat: Chat, db_session: Session) -> None:
    add_expense(db_session, "300", "Food", "Lunch", at(YESTERDAY, 13))
    add_expense(db_session, "300", "Food", "Lunch", at(today(), 13))
    chat.send(
        "Change yesterday's food expense to ₹400",
        result("ACTION", op("update_expense", {"amount": 400}, text="food", date=YESTERDAY)),
    )
    old, new = rows(db_session, Expense)
    assert (old.amount, new.amount) == (Decimal("400.00"), Decimal("300.00"))


def test_correction_uses_last_action(chat: Chat, db_session: Session) -> None:
    add_expense(db_session, "120", "Transport", "Auto", at(today(), 9))
    chat.send(
        "I spent 300 on lunch", result("ACTION", op("create_expense", {"amount": 300, "category": "Food"}))
    )
    assert chat.send("x", result("CONVERSATION", response="ok"))  # an unrelated turn in between

    chat.send(
        "Actually, it was ₹400", result("ACTION", op("update_expense", {"amount": 400}, ref="last_action"))
    )
    assert chat.fake.context()["last_action"]["intent"] == "create_expense"
    auto, lunch = rows(db_session, Expense)
    assert (auto.amount, lunch.amount) == (Decimal("120.00"), Decimal("400.00"))


def test_delete_last_expense(chat: Chat, db_session: Session) -> None:
    add_expense(db_session, "100", "Food", "Tea", at(YESTERDAY, 9))
    add_expense(db_session, "250", "Shopping", "Socks", at(YESTERDAY, 10))
    reply = chat.send("Delete my last expense", result("ACTION", op("delete_expense", ref="latest")))
    assert "Socks" in reply["pending"]["question"]
    chat.send("yes", result("ACTION", pending="confirm"))
    assert [e.description for e in rows(db_session, Expense)] == ["Tea"]


def test_list_and_daily_total(chat: Chat, db_session: Session) -> None:
    add_expense(db_session, "350.50", "Food", "Lunch", at(today(), 13))
    add_expense(db_session, "99.50", "Transport", "Metro", at(today(), 9))
    add_expense(db_session, "1000", "Bills", "Electricity", at(YESTERDAY, 9))

    t = today().isoformat()
    reply = chat.send(
        "Show my expenses today", result("QUERY", op("list_expenses", {"date_from": t, "date_to": t}))
    )
    assert [r["title"] for r in reply["parts"][0]["card"]["records"]] == ["Lunch", "Metro"]
    assert reply["parts"][0]["card"]["summary"] == "₹450 total"

    reply = chat.send("How much did I spend today?", result("QUERY", op("get_daily_expenses")))
    assert reply["text"] == "You spent ₹450 today across 2 expenses."


def test_monthly_total_and_comparison(chat: Chat, db_session: Session) -> None:
    first = today().replace(day=1)
    last_month = (first - timedelta(days=1)).replace(day=10)
    add_expense(db_session, "600", "Food", "Dinner", at(first, 20))
    add_expense(db_session, "400", "Food", "Dinner", at(last_month, 20))

    reply = chat.send("How much did I spend this month?", result("QUERY", op("get_monthly_expenses")))
    assert reply["text"].startswith(f"You spent ₹600 in {first.strftime('%B %Y')}")

    reply = chat.send("Compare this month with last month", result("QUERY", op("get_expense_comparison")))
    assert "₹600" in reply["text"] and "₹400" in reply["text"]
    assert "That's ₹200 more (+50.0%)." in reply["text"]


def test_insights_use_backend_figures(chat: Chat, db_session: Session) -> None:
    first = today().replace(day=1)
    add_expense(db_session, "700", "Food", "Groceries run", at(first, 10))
    add_expense(db_session, "300", "Transport", "Cab", at(first, 11))
    reply = chat.send(
        "Where am I spending the most?",
        result("QUERY", op("get_expense_insights")),
        "Try cooking at home a little more often.",  # the tip call
    )
    assert "Most of it went on Food: ₹700 (70%)" in reply["text"]
    assert reply["text"].endswith("Try cooking at home a little more often.")
    tip_figures = json.loads(chat.fake.calls[-1][1]["content"])
    assert tip_figures["total"] == "₹1,000"


# ======================================================================== notes


def test_note_create_then_add_to_that_note(chat: Chat, db_session: Session) -> None:
    chat.send(
        "Save a note about my FastAPI project",
        result("ACTION", op("create_note", {"title": "FastAPI project"})),
    )
    chat.send(
        "Add Docker information to that note",
        result("ACTION", op("update_note", {"append": "Docker: use a slim Python image"}, ref="last_action")),
    )
    [n] = rows(db_session, Note)
    assert (n.title, n.content) == ("FastAPI project", "Docker: use a slim Python image")


def test_delete_note_with_confirmation(chat: Chat, db_session: Session) -> None:
    add_note(db_session, "Old project ideas", "…")
    add_note(db_session, "Wi-Fi password", "…")
    chat.send("Delete my old project note", result("ACTION", op("delete_note", text="project")))
    chat.send("yes", result("ACTION", pending="confirm"))
    assert [n.title for n in rows(db_session, Note)] == ["Wi-Fi password"]


def test_search_list_and_details(chat: Chat, db_session: Session) -> None:
    add_note(db_session, "AWS setup", "IAM roles and S3 buckets")
    add_note(db_session, "Docker tips", "Use multi-stage builds")
    reply = chat.send("Find my AWS-related notes", result("QUERY", op("search_notes", {"text": "AWS"})))
    assert [r["title"] for r in reply["parts"][0]["card"]["records"]] == ["AWS setup"]

    reply = chat.send("Show all my notes", result("QUERY", op("list_notes")))
    assert len(reply["parts"][0]["card"]["records"]) == 2

    reply = chat.send(
        "What did I save about Docker?", result("QUERY", op("get_note_details", {"text": "Docker"}))
    )
    assert reply["parts"][0]["card"]["records"][0]["detail"] == "Use multi-stage builds"


# ======================================================================== cross-module & conversation


def test_multiple_operations_dont_block_each_other(chat: Chat, db_session: Session) -> None:
    reply = chat.send(
        "Add a ₹200 food expense and remind me to call Rahul",
        result(
            "ACTION",
            op("create_expense", {"amount": 200, "category": "Food"}),
            op("create_reminder", {"title": "Call Rahul"}),
        ),
    )
    assert len(rows(db_session, Expense)) == 1  # done straight away
    assert reply["pending"]["question"] == "When should I remind you?"

    chat.send(
        "tomorrow 6pm",
        result("ACTION", op("create_reminder", {"date": TOMORROW, "time": "18:00"}), pending="answer"),
    )
    assert [r.title for r in rows(db_session, NotificationTask)] == ["Call Rahul"]


def test_second_question_waits_its_turn(chat: Chat, db_session: Session) -> None:
    reply = chat.send(
        "Remind me to call Rahul and log an expense",
        result(
            "ACTION",
            op("create_reminder", {"title": "Call Rahul"}),
            op("create_expense", {"category": "Food"}),
        ),
    )
    assert reply["pending"]["question"] == "When should I remind you?"
    assert "come back to the rest" in reply["text"]

    reply = chat.send(
        "tomorrow at 9",
        result("ACTION", op("create_reminder", {"date": TOMORROW, "time": "09:00"}), pending="answer"),
    )
    assert len(rows(db_session, NotificationTask)) == 1
    assert reply["pending"]["question"] == "How much was it?"  # the queued expense now asks

    chat.send("250", result("ACTION", op("create_expense", {"amount": 250}), pending="answer"))
    [e] = rows(db_session, Expense)
    assert (e.amount, e.category) == (Decimal("250.00"), "Food")


def test_yes_only_confirms_the_latest_question(chat: Chat, db_session: Session) -> None:
    add_note(db_session, "A")
    add_note(db_session, "B")
    reply = chat.send("Delete all my notes", result("ACTION", op("delete_note", all=True)))
    assert reply["pending"]["question"] == "Are you sure you want to delete all your notes (2 notes)?"

    chat.send("What's the capital of France?", result("CONVERSATION", response="Paris."))
    reply = chat.send("Yes", result("ACTION", pending="confirm"))
    assert reply["text"].startswith("Just to be sure: Are you sure")
    assert len(rows(db_session, Note)) == 2

    chat.send("Yes", result("ACTION", pending="confirm"))
    assert rows(db_session, Note) == []


def test_forget_it_cancels(chat: Chat, db_session: Session) -> None:
    chat.send("Remind me to call Rahul", result("ACTION", op("create_reminder", {"title": "Call Rahul"})))
    reply = chat.send("Forget it", result("ACTION", pending="cancel"))
    assert reply["text"] == "Okay, I've cancelled that."
    assert [p.status for p in rows(db_session, PendingAction)] == [PendingStatus.CANCELLED]


def test_topic_change_keeps_the_pending_reminder(chat: Chat, db_session: Session) -> None:
    chat.send("Remind me to call Rahul", result("ACTION", op("create_reminder", {"title": "Call Rahul"})))
    reply = chat.send(
        "Explain FastAPI dependency injection",
        result("CONVERSATION", response="FastAPI calls your dependency functions for you..."),
    )
    assert reply["text"].startswith("FastAPI calls")
    assert rows(db_session, NotificationTask) == []
    assert [p.status for p in rows(db_session, PendingAction)] == [PendingStatus.WAITING_FOR_INFO]

    chat.send(
        "ok, tomorrow 8pm for Rahul",
        result("ACTION", op("create_reminder", {"date": TOMORROW, "time": "20:00"}), pending="answer"),
    )
    assert len(rows(db_session, NotificationTask)) == 1


def test_cancel_the_second_one_from_the_list(chat: Chat, db_session: Session) -> None:
    add_reminder(db_session, "Call Mom", at(TOMORROW, 9))
    add_reminder(db_session, "Pay rent", at(TOMORROW, 10))
    reply = chat.send("Show my reminders", result("QUERY", op("list_reminders")))
    assert [r["position"] for r in reply["parts"][0]["card"]["records"]] == [1, 2]

    chat.send("Cancel the second one", result("ACTION", op("cancel_reminder", position=2)))
    assert chat.fake.context()["last_shown_records"][1]["title"] == "Pay rent"
    assert "id" not in chat.fake.context()["last_shown_records"][1]  # Groq never sees ids
    mom, rent = rows(db_session, NotificationTask)
    assert (mom.is_cancelled, rent.is_cancelled) == (False, True)


def test_duplicate_expense_is_confirmed_first(chat: Chat, db_session: Session) -> None:
    add = result("ACTION", op("create_expense", {"amount": 200, "category": "Food", "description": "Lunch"}))
    chat.send("Spent 200 on lunch", add)
    reply = chat.send("Spent 200 on lunch", add)
    assert reply["pending"]["kind"] == "confirm"
    assert len(rows(db_session, Expense)) == 1

    chat.send("yes, I had two", result("ACTION", pending="confirm"))
    assert len(rows(db_session, Expense)) == 2


def test_retried_request_is_not_run_twice(chat: Chat, db_session: Session) -> None:
    add = result("ACTION", op("create_expense", {"amount": 90, "category": "Food"}))
    first = chat.send("Spent 90 on tea", add, client_message_id="msg-1")
    chat.conversation_id = None  # e.g. the app retried before it learned the conversation id
    again = chat.send("Spent 90 on tea", client_message_id="msg-1")  # Groq isn't called again
    assert again["message_id"] == first["message_id"] and again["text"] == first["text"]
    assert len(rows(db_session, Expense)) == 1


def test_invalid_date_is_asked_again(chat: Chat, db_session: Session) -> None:
    reply = chat.send(
        "Remind me on February 30 to pay rent",
        result("ACTION", op("create_reminder", {"title": "Pay rent", "date": "2027-02-30", "time": "09:00"})),
    )
    assert reply["pending"]["question"] == "February 30 isn't a valid date. Which date did you mean?"
    assert rows(db_session, NotificationTask) == []
    assert chat.fake.context()  # sanity: the call happened

    chat.send(
        "March 1",
        result("ACTION", op("create_reminder", {"date": "2027-03-01", "time": "09:00"}), pending="answer"),
    )
    [r] = rows(db_session, NotificationTask)
    assert r.notify_at == datetime(2027, 3, 1, 9, 0)


def test_undo_last_expense_and_undo_delete(chat: Chat, db_session: Session) -> None:
    chat.send("Add a note", result("ACTION", op("create_note", {"title": "Keep me"})))
    chat.send("Spent 50 on chai", result("ACTION", op("create_expense", {"amount": 50, "category": "Food"})))
    reply = chat.send(
        "Undo the last expense entry", result("ACTION", op("undo_last_action", {"module": "expenses"}))
    )
    assert reply["text"].startswith("Undone: removed the expense")
    assert rows(db_session, Expense) == [] and len(rows(db_session, Note)) == 1

    chat.send("Delete the keep me note", result("ACTION", op("delete_note", text="keep")))
    chat.send("yes", result("ACTION", pending="confirm"))
    assert rows(db_session, Note) == []
    chat.send("undo", result("ACTION", op("undo_last_action")))
    assert [n.title for n in rows(db_session, Note)] == ["Keep me"]

    reply = chat.send("undo", result("ACTION", op("undo_last_action", {"module": "expenses"})))
    assert reply["text"] == "There's no recent expense change to undo."


def test_undo_refuses_when_record_changed_since(chat: Chat, db_session: Session) -> None:
    chat.send("Note", result("ACTION", op("create_note", {"title": "Plan"})))
    [n] = rows(db_session, Note)
    n.content = "edited elsewhere"
    db_session.commit()
    reply = chat.send("undo", result("ACTION", op("undo_last_action")))
    assert "changed since" in reply["text"]
    assert len(rows(db_session, Note)) == 1


def test_empty_results_say_so(chat: Chat) -> None:
    t = today().isoformat()
    reply = chat.send(
        "Show my expenses today", result("QUERY", op("list_expenses", {"date_from": t, "date_to": t}))
    )
    assert reply["text"] == "You have no expenses for today."
    assert reply["parts"][0]["card"] is None


# ======================================================================== errors


def test_unreadable_groq_reply_retries_then_fails_cleanly(
    chat: Chat, client: TestClient, db_session: Session
) -> None:
    chat.fake.replies.extend(["not json", '{"type": "NONSENSE"}'])
    res = client.post(f"{API}/chat", json={"message": "hi"}, headers=auth_header(chat.token))
    assert res.status_code == 503 and res.json()["code"] == "ai_unavailable"
    assert len(chat.fake.calls) == 2
    assert rows(db_session, Message) == []  # nothing saved, so sending again is safe


def test_bad_first_reply_is_retried(chat: Chat) -> None:
    reply = chat.send("hello", "oops", result("CONVERSATION", response="Hi there!"))
    assert reply["text"] == "Hi there!"


def test_unsupported_intent_becomes_fallback(chat: Chat) -> None:
    reply = chat.send("Book me a cab", result("ACTION", op("book_cab", {"to": "airport"})))
    assert reply["type"] == "FALLBACK"
    assert "reminders, expenses and notes" in reply["text"]


def test_groq_failure_is_friendly_and_saves_nothing(
    client: TestClient, fake: FakeGroq, db_session: Session
) -> None:
    from app.core.exceptions import AIServiceError

    token = login(client)["access_token"]
    fake.replies.append(AIServiceError("That took too long to think about. Please try again."))
    res = client.post(f"{API}/chat", json={"message": "Spent 50 on tea"}, headers=auth_header(token))
    assert res.status_code == 503
    assert res.json() == {
        "detail": "That took too long to think about. Please try again.",
        "code": "ai_unavailable",
    }
    assert rows(db_session, Expense) == []


def test_groq_client_maps_sdk_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.core.exceptions import AIServiceError

    request = httpx.Request("POST", "https://api.groq.com")
    errors = {
        "a lot of requests": groq.RateLimitError(
            "slow", response=httpx.Response(429, request=request), body=None
        ),
        "too long": groq.APITimeoutError(request=request),
        "can't reach": groq.APIConnectionError(request=request),
    }
    monkeypatch.setattr(settings, "GROQ_API_KEY", SecretStr("k"))
    for message, error in errors.items():

        class Completions:
            async def create(self, _error: Exception = error, **_: Any) -> None:
                raise _error

        client = type("Client", (), {"chat": type("Chat", (), {"completions": Completions()})()})()
        monkeypatch.setattr(groq_client, "get_client", lambda c=client: c)
        with pytest.raises(AIServiceError, match=message):
            asyncio.run(groq_client.chat_completion([{"role": "user", "content": "hi"}]))


def test_missing_api_key(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "GROQ_API_KEY", SecretStr(""))
    token = login(client)["access_token"]
    res = client.post(f"{API}/chat", json={"message": "hello"}, headers=auth_header(token))
    assert res.status_code == 503 and "GROQ_API_KEY" in res.json()["detail"]


def test_expired_pending_action(chat: Chat, db_session: Session) -> None:
    chat.send("Remind me to call Rahul", result("ACTION", op("create_reminder", {"title": "Call Rahul"})))
    [p] = rows(db_session, PendingAction)
    p.expires_at = datetime(2000, 1, 1)
    db_session.commit()

    reply = chat.send(
        "tomorrow 8pm", result("ACTION", op("create_reminder", {"time": "20:00"}), pending="answer")
    )
    assert reply["text"] == "Sorry, that earlier request timed out. Could you tell me again in full?"
    assert chat.fake.context()["expired_pending_action"]["intent"] == "create_reminder"
    assert [p.status for p in rows(db_session, PendingAction)] == [PendingStatus.EXPIRED]


def test_other_users_conversation_is_not_found(client: TestClient, fake: FakeGroq) -> None:
    alice = Chat(client, fake, "9000000001")
    alice.send("hi", result("CONVERSATION", response="Hi"))
    bob = Chat(client, fake, "9000000002")
    bob.conversation_id = alice.conversation_id
    res = client.post(
        f"{API}/chat",
        json={"message": "show it", "conversation_id": alice.conversation_id},
        headers=auth_header(bob.token),
    )
    assert res.status_code == 404


def test_other_users_records_are_never_targeted(
    client: TestClient, fake: FakeGroq, db_session: Session
) -> None:
    alice = Chat(client, fake, "9000000001")
    alice.send("Note", result("ACTION", op("create_note", {"title": "Alice secret"})))
    bob = Chat(client, fake, "9000000002")
    reply = bob.send("Delete my secret note", result("ACTION", op("delete_note", text="secret")))
    assert reply["text"] == "I couldn't find a note matching “secret”."
    assert len(rows(db_session, Note)) == 1


def test_debug_trace_is_returned(chat: Chat) -> None:
    reply = chat.send("hi", result("CONVERSATION", response="Hello!"))
    steps = [s["step"] for s in reply["debug"]]
    for expected in (
        "received",
        "context",
        "groq.request",
        "groq.response",
        "classified",
        "route.conversation",
        "reply.saved",
    ):
        assert expected in steps
    sent = next(s for s in reply["debug"] if s["step"] == "groq.request")
    assert sent["purpose"] == "classify"
    assert [m["role"] for m in sent["messages"]] == ["system", "system", "user"]  # prompt, CONTEXT, message
    assert sent["messages"][-1]["content"] == "hi"
    got = next(s for s in reply["debug"] if s["step"] == "groq.response")
    assert json.loads(got["response"])["response"] == "Hello!"
    assert all(isinstance(s["ms"], int) for s in reply["debug"])


def test_debug_trace_shows_the_retry(chat: Chat) -> None:
    reply = chat.send("hello", "oops", result("CONVERSATION", response="Hi there!"))
    responses = [s for s in reply["debug"] if s["step"] == "groq.response"]
    assert [r["attempt"] for r in responses] == [1, 2]
    assert "invalid" in responses[0] and "invalid" not in responses[1]


def test_debug_trace_hidden_when_off(chat: Chat, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "CHAT_DEBUG", False)
    assert chat.send("hi", result("CONVERSATION", response="Hello!"))["debug"] is None


def test_chat_requires_login(client: TestClient) -> None:
    assert client.post(f"{API}/chat", json={"message": "hello"}).status_code == 401


def test_stale_position_that_contradicts_the_words_is_ignored(chat: Chat, db_session: Session) -> None:
    add_reminder(db_session, "Call Mom", at(TOMORROW, 9))
    add_reminder(db_session, "Call Rahul", at(TOMORROW, 20))
    chat.send("Show my reminders", result("QUERY", op("list_reminders")))
    # Groq sent both the words and an unrelated list number
    chat.send(
        "Change Rahul's reminder to 9 PM",
        result("ACTION", op("update_reminder", {"time": "21:00"}, text="Rahul", position=1)),
    )
    mom, rahul = rows(db_session, NotificationTask)
    assert (mom.notify_at, rahul.notify_at) == (at(TOMORROW, 9), at(TOMORROW, 21))


def test_quick_actions_skip_groq(chat: Chat, client: TestClient, db_session: Session) -> None:
    add_reminder(db_session, "Call Mom", at(today(), 23, 59))
    add_reminder(db_session, "Pay rent", at(TOMORROW, 10))
    add_note(db_session, "Wi-Fi password", "ask landlord")

    def tap(action: str, text: str) -> dict[str, Any]:
        body = {"message": text, "conversation_id": chat.conversation_id, "quick_action": action}
        res = client.post(f"{API}/chat", json=body, headers=auth_header(chat.token))
        assert res.status_code == 200, res.text
        chat.conversation_id = res.json()["conversation_id"]
        return res.json()

    today_reply = tap("today", "What's on my plate today?")
    assert [r["title"] for r in today_reply["parts"][0]["card"]["records"]] == ["Call Mom"]
    reminders = tap("reminders", "Show my reminders")
    assert [r["title"] for r in reminders["parts"][0]["card"]["records"]] == ["Call Mom", "Pay rent"]
    assert tap("notes", "Show my notes")["parts"][0]["card"]["records"][0]["title"] == "Wi-Fi password"
    assert tap("expenses", "Show my expenses")["text"] == "You have no expenses."
    assert chat.fake.calls == []  # Groq was never called

    # the list a button showed still works as context for the next typed message
    tap("reminders", "Show my reminders")
    chat.send("Cancel the second one", result("ACTION", op("cancel_reminder", position=2)))
    assert [r.is_cancelled for r in rows(db_session, NotificationTask)] == [False, True]
