import pytest
from pydantic import ValidationError

from app.core.config import Settings

GOOD = {
    "ENVIRONMENT": "production",
    "JWT_SECRET_KEY": "a-real-secret-that-is-at-least-32-characters-long",
    "DB_PASSWORD": "real-db-password",
    "GROQ_API_KEY": "real-groq-key",
    "CORS_ORIGINS": "https://app.example.com",
    "DATABASE_URL": "",  # conftest sets one for the test database; production here uses DB_* parts
}


def settings(**overrides: str) -> Settings:
    # _env_file=None: only the values given here, not the developer's .env
    return Settings(_env_file=None, **{**GOOD, **overrides})  # type: ignore[arg-type, call-arg]


def test_production_accepts_real_secrets() -> None:
    assert settings().is_production


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"JWT_SECRET_KEY": "change-me-to-a-long-random-string-of-32-plus-chars"}, "JWT_SECRET_KEY"),
        ({"DB_PASSWORD": "change-me"}, "DB_PASSWORD"),
        ({"DB_PASSWORD": ""}, "DB_PASSWORD"),
        ({"GROQ_API_KEY": ""}, "GROQ_API_KEY"),
    ],
)
def test_production_refuses_missing_or_placeholder_secrets(overrides: dict[str, str], message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        settings(**overrides)


def test_database_url_replaces_db_password() -> None:
    assert settings(DB_PASSWORD="", DATABASE_URL="mysql+pymysql://u:p@db/taskmon").is_production


def test_missing_jwt_secret_is_a_clear_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JWT_SECRET_KEY")
    with pytest.raises(ValidationError, match="JWT_SECRET_KEY"):
        Settings(_env_file=None, ENVIRONMENT="local")  # type: ignore[call-arg]


def test_local_development_needs_no_production_secrets() -> None:
    assert not Settings(_env_file=None, JWT_SECRET_KEY="x" * 32).is_production  # type: ignore[call-arg]
