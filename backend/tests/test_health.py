from fastapi.testclient import TestClient


def test_liveness(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_readiness_checks_database(client: TestClient) -> None:
    res = client.get("/health/ready")
    assert res.status_code == 200
    assert res.json() == {"status": "ok", "database": "up"}


def test_request_id_is_generated_and_echoed(client: TestClient) -> None:
    assert len(client.get("/health").headers["X-Request-ID"]) == 32
    res = client.get("/health", headers={"X-Request-ID": "upstream-abc.123"})
    assert res.headers["X-Request-ID"] == "upstream-abc.123"


def test_cors_preflight_allows_frontend(client: TestClient) -> None:
    res = client.options(
        "/api/v1/auth/send-otp",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "http://localhost:5173"
