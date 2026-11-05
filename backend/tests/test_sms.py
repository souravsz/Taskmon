"""Bank SMS → expense, daily budget and the over-budget warning push (Firebase faked)."""

from datetime import datetime
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DeviceToken, Expense
from app.services import push_service, sms_service
from tests.conftest import API, auth_header, login

# The real SMS from the user's bank
SMS = (
    "Debited Rs 50.00 from a/c X9844 on 04Nov26 12:57 via UPI to SAFIYA HASSA. Ref 630830086298. "
    "Bal Rs 407.64. Not you? Call 18004251199 -Federal Bank"
)


def sms(
    amount: str = "50.00", ref: str = "630830086298", to: str = "SAFIYA HASSA", time: str = "12:57"
) -> str:
    return (
        SMS.replace("50.00", amount)
        .replace("630830086298", ref)
        .replace("SAFIYA HASSA", to)
        .replace("12:57", time)
    )


@pytest.fixture(autouse=True)
def today_is_the_sms_day(monkeypatch: pytest.MonkeyPatch) -> None:
    """The user's "now" is the day of the sample SMS, so its payment counts as today's."""
    monkeypatch.setattr(sms_service, "local_now", lambda _user: datetime(2026, 11, 4, 13, 0))


@pytest.fixture
def pushes(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str, str]]:
    sent: list[tuple[str, str, str]] = []

    def fake_send(
        token: str, title: str, text: str, data: dict[str, str], category: str | None = None
    ) -> str:
        sent.append((token, title, text))
        return "sent"

    monkeypatch.setattr(push_service, "send", fake_send)
    return sent


def logged_in(client: TestClient, db: Session, budget: str | None = None) -> dict[str, str]:
    me = login(client)
    headers = auth_header(me["access_token"])
    if budget:
        assert (
            client.put(
                f"{API}/users/me/daily-budget", json={"daily_budget": budget}, headers=headers
            ).status_code
            == 200
        )
    db.add(DeviceToken(user_id=me["user"]["id"], token="phone-1", platform="android"))
    db.commit()
    return headers


# ======================================================================== parsing


def test_parse_the_federal_bank_debit() -> None:
    debit = sms_service.parse(SMS)
    assert debit is not None
    assert debit.amount == Decimal("50.00")
    assert debit.spent_at == datetime(2026, 11, 4, 12, 57)
    assert (debit.method, debit.recipient, debit.account, debit.reference) == (
        "UPI",
        "SAFIYA HASSA",
        "X9844",
        "630830086298",
    )


def test_parse_handles_line_breaks_and_thousands() -> None:
    debit = sms_service.parse(sms(amount="1,250.50").replace(" Ref ", "\nRef "))
    assert debit is not None and debit.amount == Decimal("1250.50")


@pytest.mark.parametrize(
    "text",
    [
        "Credited Rs 50.00 to a/c X9844 on 04Nov26 12:57 via UPI from SAFIYA HASSA. Ref 1. -Federal Bank",
        SMS.replace("-Federal Bank", "-Other Bank"),
        "Your OTP is 123456",
        SMS.replace("04Nov26", "31Feb26"),  # impossible date
    ],
)
def test_other_messages_are_not_debits(text: str) -> None:
    assert sms_service.parse(text) is None


# ======================================================================== endpoint


def test_bank_sms_becomes_an_expense(client: TestClient, db_session: Session, pushes: list) -> None:
    headers = logged_in(client, db_session)
    res = client.post(f"{API}/sms/bank", json={"text": SMS}, headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["recorded"] and body["reason"] == "recorded"
    assert Decimal(body["amount"]) == Decimal("50.00")

    [e] = db_session.scalars(select(Expense)).all()
    assert (e.amount, e.category, e.spent_at, e.reference) == (
        Decimal("50.00"),
        "Misc",
        datetime(2026, 11, 4, 12, 57),
        "630830086298",
    )
    assert e.description == "UPI to SAFIYA HASSA · Federal Bank X9844"
    assert pushes == []  # no budget set, so no warning


def test_same_sms_twice_is_recorded_once(client: TestClient, db_session: Session, pushes: list) -> None:
    headers = logged_in(client, db_session)
    client.post(f"{API}/sms/bank", json={"text": SMS}, headers=headers)
    res = client.post(f"{API}/sms/bank", json={"text": SMS}, headers=headers)
    assert res.json()["recorded"] is False and res.json()["reason"] == "already_recorded"
    assert len(db_session.scalars(select(Expense)).all()) == 1


def test_other_text_is_ignored(client: TestClient, db_session: Session, pushes: list) -> None:
    headers = logged_in(client, db_session)
    res = client.post(f"{API}/sms/bank", json={"text": "Your OTP is 123456"}, headers=headers)
    assert res.json() == {**res.json(), "recorded": False, "reason": "not_a_federal_bank_debit"}
    assert db_session.scalars(select(Expense)).all() == []


def test_bank_sms_needs_login(client: TestClient) -> None:
    assert client.post(f"{API}/sms/bank", json={"text": SMS}).status_code == 401


# ======================================================================== daily budget


def test_set_daily_budget_and_see_it_at_login(client: TestClient) -> None:
    me = login(client)
    assert me["user"]["daily_budget"] is None
    res = client.put(
        f"{API}/users/me/daily-budget", json={"daily_budget": 500}, headers=auth_header(me["access_token"])
    )
    assert res.status_code == 200 and Decimal(res.json()["daily_budget"]) == Decimal("500")
    assert Decimal(login(client)["user"]["daily_budget"]) == Decimal("500")


@pytest.mark.parametrize("amount", [0, -10, "abc"])
def test_daily_budget_must_be_positive(client: TestClient, amount: object) -> None:
    token = login(client)["access_token"]
    res = client.put(
        f"{API}/users/me/daily-budget", json={"daily_budget": amount}, headers=auth_header(token)
    )
    assert res.status_code == 422


def test_over_budget_sends_a_warning(client: TestClient, db_session: Session, pushes: list) -> None:
    headers = logged_in(client, db_session, budget="80")
    first = client.post(f"{API}/sms/bank", json={"text": sms("50.00", ref="1")}, headers=headers).json()
    assert first["over_budget"] is False and pushes == []

    second = client.post(
        f"{API}/sms/bank", json={"text": sms("40.00", ref="2", to="CHAI POINT")}, headers=headers
    )
    body = second.json()
    assert body["over_budget"] is True
    assert Decimal(body["spent_today"]) == Decimal("90.00")
    assert pushes == [
        (
            "phone-1",
            "Daily budget exceeded",
            "You've spent ₹90 today, over your ₹80 budget. Last: ₹40 to CHAI POINT.",
        )
    ]


def test_budget_counts_only_that_day(client: TestClient, db_session: Session, pushes: list) -> None:
    headers = logged_in(client, db_session, budget="80")
    client.post(f"{API}/sms/bank", json={"text": sms("70.00", ref="1")}, headers=headers)
    other_day = sms("70.00", ref="2").replace("04Nov26", "05Nov26")
    assert (
        client.post(f"{API}/sms/bank", json={"text": other_day}, headers=headers).json()["over_budget"]
        is False
    )


def test_old_payment_caught_up_later_records_but_does_not_warn(
    client: TestClient, db_session: Session, pushes: list
) -> None:
    """Inbox sync after being offline sends days-old SMS: recorded, but a warning about a past day is noise."""
    headers = logged_in(client, db_session, budget="10")
    old = sms("50.00", ref="9").replace("04Nov26", "01Nov26")
    body = client.post(f"{API}/sms/bank", json={"text": old}, headers=headers).json()
    assert body["recorded"] and body["over_budget"] is True
    assert pushes == []


def test_push_failure_still_records_the_expense(
    client: TestClient, db_session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(*_: object, **__: object) -> str:
        raise RuntimeError("FIREBASE_CREDENTIALS_FILE is not set")

    monkeypatch.setattr(push_service, "send", broken)
    headers = logged_in(client, db_session, budget="10")
    res = client.post(f"{API}/sms/bank", json={"text": SMS}, headers=headers)
    assert res.status_code == 200 and res.json()["over_budget"] is True
    assert len(db_session.scalars(select(Expense)).all()) == 1
