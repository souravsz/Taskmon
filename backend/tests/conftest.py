import os

# Must be set before the app (and its settings) are imported.
os.environ.update(
    ENVIRONMENT="test",
    DATABASE_URL="sqlite://",
    JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-characters",
    STATIC_OTP="1234",
    LOG_LEVEL="WARNING",
    CORS_ORIGINS="http://localhost:5173",
)

from collections.abc import Generator  # noqa: E402

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.models  # noqa: E402, F401
from app.database.base import Base  # noqa: E402
from app.database.connection import get_db  # noqa: E402
from app.main import app  # noqa: E402

API = "/api/v1"


@pytest.fixture
def db_session() -> Generator[Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def login(client: TestClient, mobile: str = "9876543210") -> dict:
    res = client.post(f"{API}/auth/verify-otp", json={"mobile_number": mobile, "otp": "1234"})
    assert res.status_code == 200, res.text
    return res.json()


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
