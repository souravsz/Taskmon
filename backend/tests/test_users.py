from datetime import timedelta

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from tests.conftest import API, auth_header, login


def test_me_requires_token(client: TestClient) -> None:
    res = client.get(f"{API}/users/me")
    assert res.status_code == 401
    assert res.json()["code"] == "unauthorized"


def test_me_rejects_garbage_token(client: TestClient) -> None:
    res = client.get(f"{API}/users/me", headers=auth_header("not-a-jwt"))
    assert res.status_code == 401
    assert res.json()["code"] == "invalid_token"


def test_me_rejects_expired_token(client: TestClient) -> None:
    user_id = login(client)["user"]["id"]
    expired = create_access_token(user_id, expires_delta=timedelta(seconds=-1))
    res = client.get(f"{API}/users/me", headers=auth_header(expired))
    assert res.status_code == 401
    assert res.json()["detail"] == "Token has expired"


def test_set_username_then_login_reports_it(client: TestClient) -> None:
    token = login(client)["access_token"]

    res = client.put(f"{API}/users/me/username", json={"username": " john_doe "}, headers=auth_header(token))
    assert res.status_code == 200
    assert res.json()["username"] == "john_doe"

    again = login(client)
    assert again["has_username"] is True
    assert again["user"]["username"] == "john_doe"


def test_setting_same_username_again_is_idempotent(client: TestClient) -> None:
    token = login(client)["access_token"]
    for _ in range(2):
        res = client.put(
            f"{API}/users/me/username", json={"username": "john_doe"}, headers=auth_header(token)
        )
        assert res.status_code == 200


def test_duplicate_username_conflicts(client: TestClient) -> None:
    first = login(client, "9876543210")["access_token"]
    second = login(client, "9123456789")["access_token"]
    client.put(f"{API}/users/me/username", json={"username": "john_doe"}, headers=auth_header(first))

    res = client.put(f"{API}/users/me/username", json={"username": "john_doe"}, headers=auth_header(second))
    assert res.status_code == 409
    assert res.json() == {"detail": "Username already taken", "code": "username_taken"}


def test_invalid_username_is_rejected(client: TestClient) -> None:
    token = login(client)["access_token"]
    for bad in ["ab", "has space", "x" * 31, "emoji😀"]:
        res = client.put(f"{API}/users/me/username", json={"username": bad}, headers=auth_header(token))
        assert res.status_code == 422, bad
