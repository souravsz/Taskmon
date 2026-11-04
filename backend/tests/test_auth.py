import pytest
from fastapi.testclient import TestClient

from tests.conftest import API, login


def test_send_otp(client: TestClient) -> None:
    res = client.post(f"{API}/auth/send-otp", json={"mobile_number": "9876543210"})
    assert res.status_code == 200
    assert res.json() == {"message": "OTP sent"}


@pytest.mark.parametrize("bad", ["12345", "abcdefghij", "+0123456789", "1" * 20])
def test_send_otp_rejects_invalid_numbers(client: TestClient, bad: str) -> None:
    res = client.post(f"{API}/auth/send-otp", json={"mobile_number": bad})
    assert res.status_code == 422
    assert res.json()["code"] == "validation_error"


def test_wrong_otp_is_rejected(client: TestClient) -> None:
    res = client.post(f"{API}/auth/verify-otp", json={"mobile_number": "9876543210", "otp": "0000"})
    assert res.status_code == 401
    assert res.json() == {"detail": "Invalid OTP", "code": "invalid_otp"}
    assert res.headers["WWW-Authenticate"] == "Bearer"


def test_first_login_creates_user_without_username(client: TestClient) -> None:
    body = login(client)
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["expires_in"] > 0
    assert body["has_username"] is False
    assert body["user"]["mobile_number"] == "+919876543210"
    assert body["user"]["username"] is None


@pytest.mark.parametrize("variant", ["9876543210", "+919876543210", "919876543210", "+91 98765-43210"])
def test_mobile_formats_resolve_to_same_user(client: TestClient, variant: str) -> None:
    first = login(client, "9876543210")
    again = login(client, variant)
    assert again["user"]["id"] == first["user"]["id"]
