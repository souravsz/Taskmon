"""Push notifications: device token endpoints, the reminder worker and the FCM sender (Firebase faked)."""

from datetime import UTC, datetime
from typing import Any

import pytest
import requests
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import worker
from app.models import DeviceToken, NotificationTask, User
from app.services import push_service
from tests.conftest import API, auth_header, login

# Thursday 2026-11-05, 10:00 UTC = 15:30 in Asia/Kolkata (the default user timezone)
NOW_UTC = datetime(2026, 11, 5, 10, 0, tzinfo=UTC)
LOCAL_NOW = datetime(2026, 11, 5, 15, 30)


class FakePush:
    """Stands in for push_service.send: records each push and answers with a preset result per token."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str, str, dict[str, str], str | None]] = []
        self.results: dict[str, str] = {}

    def __call__(
        self, token: str, title: str, text: str, data: dict[str, str], category: str | None = None
    ) -> str:
        self.sent.append((token, title, text, data, category))
        return self.results.get(token, "sent")


@pytest.fixture
def push(monkeypatch: pytest.MonkeyPatch) -> FakePush:
    fake = FakePush()
    monkeypatch.setattr(push_service, "send", fake)
    return fake


def add_user(db: Session, mobile: str = "+919876543210", timezone: str = "Asia/Kolkata") -> User:
    user = User(mobile_number=mobile, username=f"u{mobile[-4:]}", timezone=timezone)
    db.add(user)
    db.flush()
    return user


def add_phone(db: Session, user: User, phone: str = "phone-1") -> None:
    db.add(DeviceToken(user_id=user.id, token=phone, platform="android"))
    db.flush()


def add_reminder(
    db: Session, user: User, at: datetime, title: str = "Call Rahul", **fields: Any
) -> NotificationTask:
    reminder = NotificationTask(user_id=user.id, title=title, notify_at=at, **fields)
    db.add(reminder)
    db.commit()
    return reminder


# ======================================================================== device endpoints


def test_register_and_unregister_a_phone(client: TestClient, db_session: Session) -> None:
    token = login(client)["access_token"]
    res = client.post(f"{API}/devices", json={"token": "fcm-abc"}, headers=auth_header(token))
    assert res.status_code == 204
    res = client.post(
        f"{API}/devices", json={"token": "fcm-abc"}, headers=auth_header(token)
    )  # again: no dup
    assert res.status_code == 204
    [device] = db_session.scalars(select(DeviceToken)).all()
    assert (device.token, device.platform) == ("fcm-abc", "android")

    res = client.post(f"{API}/devices/unregister", json={"token": "fcm-abc"}, headers=auth_header(token))
    assert res.status_code == 204
    assert db_session.scalars(select(DeviceToken)).all() == []


def test_phone_moves_to_the_account_that_logs_in(client: TestClient, db_session: Session) -> None:
    alice = login(client, "9876543210")
    bob = login(client, "9123456789")
    client.post(f"{API}/devices", json={"token": "shared-phone"}, headers=auth_header(alice["access_token"]))
    client.post(f"{API}/devices", json={"token": "shared-phone"}, headers=auth_header(bob["access_token"]))
    [device] = db_session.scalars(select(DeviceToken)).all()
    assert device.user_id == bob["user"]["id"]


def test_done_button_completes_the_reminder(client: TestClient, db_session: Session) -> None:
    me = login(client)
    user = db_session.get(User, me["user"]["id"])
    assert user is not None
    reminder = add_reminder(db_session, user, LOCAL_NOW)

    url = f"{API}/reminders/{reminder.id}/complete"
    assert client.post(url, headers=auth_header(me["access_token"])).status_code == 204
    db_session.refresh(reminder)
    assert reminder.is_completed


def test_cannot_complete_someone_elses_reminder(client: TestClient, db_session: Session) -> None:
    other = add_reminder(db_session, add_user(db_session, "+919000000001"), LOCAL_NOW)
    token = login(client)["access_token"]
    res = client.post(f"{API}/reminders/{other.id}/complete", headers=auth_header(token))
    assert res.status_code == 404
    db_session.refresh(other)
    assert not other.is_completed


def test_device_endpoints_need_login_and_a_token(client: TestClient) -> None:
    assert client.post(f"{API}/devices", json={"token": "x"}).status_code == 401
    token = login(client)["access_token"]
    assert client.post(f"{API}/devices", json={"token": ""}, headers=auth_header(token)).status_code == 422


# ======================================================================== worker


def test_due_reminder_is_pushed_and_marked_done(db_session: Session, push: FakePush) -> None:
    user = add_user(db_session)
    add_phone(db_session, user)
    reminder = add_reminder(db_session, user, LOCAL_NOW)

    assert worker.run_once(db_session, NOW_UTC) == 1
    data = {"type": "reminder", "reminder_id": str(reminder.id)}
    assert push.sent == [("phone-1", "Call Rahul", "Reminder · 3:30 PM", data, "reminder")]  # with Done
    assert reminder.is_notified and reminder.notified_at == LOCAL_NOW
    assert worker.run_once(db_session, NOW_UTC) == 0  # not sent twice


def test_future_cancelled_and_completed_reminders_are_not_pushed(db_session: Session, push: FakePush) -> None:
    user = add_user(db_session)
    add_phone(db_session, user)
    add_reminder(db_session, user, datetime(2026, 11, 5, 15, 31))
    add_reminder(db_session, user, LOCAL_NOW, is_cancelled=True)
    add_reminder(db_session, user, LOCAL_NOW, is_completed=True)

    assert worker.run_once(db_session, NOW_UTC) == 0
    assert push.sent == []


def test_daily_reminder_moves_to_tomorrow(db_session: Session, push: FakePush) -> None:
    user = add_user(db_session)
    add_phone(db_session, user)
    reminder = add_reminder(db_session, user, LOCAL_NOW, recurrence="daily")

    worker.run_once(db_session, NOW_UTC)
    [(*_, category)] = push.sent
    assert category is None  # no Done button: it would stop every future repeat
    assert reminder.notify_at == datetime(2026, 11, 6, 15, 30)
    assert not reminder.is_notified  # stays open for the next repeat


def test_weekday_reminder_on_friday_moves_to_monday(db_session: Session, push: FakePush) -> None:
    user = add_user(db_session)
    reminder = add_reminder(db_session, user, datetime(2026, 11, 6, 9, 0), recurrence="weekdays")

    worker.run_once(db_session, datetime(2026, 11, 6, 3, 30, tzinfo=UTC))  # Friday 09:00 IST
    assert reminder.notify_at == datetime(2026, 11, 9, 9, 0)  # Monday


def test_dead_phone_token_is_removed(db_session: Session, push: FakePush) -> None:
    user = add_user(db_session)
    add_phone(db_session, user, "old-phone")
    add_phone(db_session, user, "new-phone")
    push.results["old-phone"] = "dead"
    reminder = add_reminder(db_session, user, LOCAL_NOW)

    worker.run_once(db_session, NOW_UTC)
    assert db_session.scalars(select(DeviceToken.token)).all() == ["new-phone"]
    assert reminder.is_notified


def test_fcm_trouble_retries_on_the_next_run(db_session: Session, push: FakePush) -> None:
    user = add_user(db_session)
    add_phone(db_session, user)
    reminder = add_reminder(db_session, user, LOCAL_NOW)

    push.results["phone-1"] = "failed"
    worker.run_once(db_session, NOW_UTC)
    assert not reminder.is_notified

    push.results["phone-1"] = "sent"
    worker.run_once(db_session, NOW_UTC)
    assert reminder.is_notified and len(push.sent) == 2


def test_user_without_a_phone_is_marked_done(db_session: Session, push: FakePush) -> None:
    reminder = add_reminder(db_session, add_user(db_session), LOCAL_NOW)
    worker.run_once(db_session, NOW_UTC)
    assert push.sent == [] and reminder.is_notified


def test_reminder_over_an_hour_late_is_skipped(db_session: Session, push: FakePush) -> None:
    user = add_user(db_session)
    add_phone(db_session, user)
    reminder = add_reminder(db_session, user, datetime(2026, 11, 5, 14, 0))  # 90 minutes ago

    worker.run_once(db_session, NOW_UTC)
    assert push.sent == [] and reminder.is_notified


def test_due_is_checked_in_each_users_timezone(db_session: Session, push: FakePush) -> None:
    london = add_user(db_session, "+447700900123", timezone="UTC")
    india = add_user(db_session)
    add_phone(db_session, london, "london-phone")
    add_phone(db_session, india, "india-phone")
    add_reminder(db_session, london, datetime(2026, 11, 5, 10, 0))  # 10:00 UTC: now
    add_reminder(db_session, india, datetime(2026, 11, 5, 16, 0))  # 16:00 IST: in 30 minutes

    worker.run_once(db_session, NOW_UTC)
    assert [token for token, *_ in push.sent] == ["london-phone"]


# ======================================================================== FCM sender


class FakeSession:
    def __init__(self, status: int = 200, text: str = "{}", error: Exception | None = None) -> None:
        self.status, self.text, self.error = status, text, error
        self.posted: dict[str, Any] = {}

    def post(self, url: str, json: dict[str, Any], timeout: int) -> requests.Response:
        if self.error:
            raise self.error
        self.posted = {"url": url, "json": json}
        res = requests.Response()
        res.status_code, res._content = self.status, self.text.encode()
        return res


@pytest.mark.parametrize(
    ("status", "text", "expected"),
    [
        (200, '{"name": "projects/p/messages/1"}', "sent"),
        (404, '{"error": {"status": "NOT_FOUND", "details": [{"errorCode": "UNREGISTERED"}]}}', "dead"),
        (
            400,
            '{"error": {"message": "The registration token is not a valid FCM registration token"}}',
            "dead",
        ),
        (500, '{"error": {"status": "INTERNAL"}}', "failed"),
        (401, '{"error": {"status": "UNAUTHENTICATED"}}', "failed"),
    ],
)
def test_fcm_replies(monkeypatch: pytest.MonkeyPatch, status: int, text: str, expected: str) -> None:
    session = FakeSession(status, text)
    monkeypatch.setattr(push_service, "_fcm", lambda: (session, "https://fcm/send"))
    assert push_service.send("tok", "Call Rahul", "Reminder · 3:30 PM", {"type": "reminder"}) == expected


def test_fcm_message_is_data_only_with_the_done_category(monkeypatch: pytest.MonkeyPatch) -> None:
    """Data-only, so the app's expo-notifications draws it and can add the Done button."""
    session = FakeSession()
    monkeypatch.setattr(push_service, "_fcm", lambda: (session, "https://fcm/send"))
    push_service.send("tok", "Call Rahul", "Reminder · 3:30 PM", {"reminder_id": "7"}, "reminder")
    assert session.posted["json"]["message"] == {
        "token": "tok",
        "data": {
            "title": "Call Rahul",
            "message": "Reminder · 3:30 PM",
            "channelId": "reminders",
            "body": '{"reminder_id": "7"}',
            "categoryId": "reminder",
        },
        "android": {"priority": "high"},
    }


def test_fcm_message_without_a_category_has_no_buttons(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession()
    monkeypatch.setattr(push_service, "_fcm", lambda: (session, "https://fcm/send"))
    push_service.send("tok", "Exercise", "Reminder · 8:00 AM", {})
    assert "categoryId" not in session.posted["json"]["message"]["data"]


def test_fcm_unreachable_is_a_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    session = FakeSession(error=requests.ConnectionError("no network"))
    monkeypatch.setattr(push_service, "_fcm", lambda: (session, "https://fcm/send"))
    assert push_service.send("tok", "t", "b", {}) == "failed"
