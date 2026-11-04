from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Expense, Note, NotificationTask
from tests.conftest import API, auth_header, login

NOW = datetime(2026, 11, 4, 12, 0)


def _seed(db: Session, user_id: int) -> None:
    db.add_all(
        [
            NotificationTask(user_id=user_id, title=f"Reminder {i}", notify_at=NOW + timedelta(hours=i))
            for i in range(5)
        ]
        + [
            Expense(
                user_id=user_id,
                amount=Decimal("100.50") * (i + 1),
                category="Food",
                spent_at=NOW - timedelta(days=i),
            )
            for i in range(3)
        ]
        + [Note(user_id=user_id, title=f"Note {i}") for i in range(4)]
    )
    db.commit()


@pytest.fixture
def token(client: TestClient, db_session: Session) -> str:
    body = login(client)
    _seed(db_session, body["user"]["id"])
    return body["access_token"]


@pytest.mark.parametrize("resource", ["reminders", "expenses", "notes"])
def test_lists_require_auth(client: TestClient, resource: str) -> None:
    assert client.get(f"{API}/{resource}").status_code == 401


def test_reminders_paginate_soonest_first(client: TestClient, token: str) -> None:
    first = client.get(f"{API}/reminders", params={"limit": 2}, headers=auth_header(token)).json()
    assert [r["title"] for r in first["items"]] == ["Reminder 0", "Reminder 1"]
    assert (first["total"], first["offset"], first["has_more"]) == (5, 0, True)

    last = client.get(f"{API}/reminders", params={"limit": 2, "offset": 4}, headers=auth_header(token)).json()
    assert [r["title"] for r in last["items"]] == ["Reminder 4"]
    assert last["has_more"] is False
    assert last["items"][0]["is_notified"] is False


def test_expenses_newest_first_with_total(client: TestClient, token: str) -> None:
    page = client.get(f"{API}/expenses", params={"limit": 2}, headers=auth_header(token)).json()
    assert [e["amount"] for e in page["items"]] == ["100.50", "201.00"]
    assert page["total_amount"] == "603.00"
    assert page["has_more"] is True


def test_notes_page(client: TestClient, token: str) -> None:
    page = client.get(f"{API}/notes", params={"limit": 10}, headers=auth_header(token)).json()
    assert page["total"] == 4
    assert page["has_more"] is False


def test_users_only_see_their_own_rows(client: TestClient, token: str) -> None:
    other = login(client, "9123456789")["access_token"]
    for resource in ("reminders", "expenses", "notes"):
        page = client.get(f"{API}/{resource}", headers=auth_header(other)).json()
        assert page["items"] == [] and page["total"] == 0


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}])
def test_invalid_page_params(client: TestClient, token: str, params: dict) -> None:
    res = client.get(f"{API}/notes", params=params, headers=auth_header(token))
    assert res.status_code == 422
