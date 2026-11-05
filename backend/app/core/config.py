from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    ENVIRONMENT: Literal["local", "test", "staging", "production"] = "local"
    APP_NAME: str = "Task Mon API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    DOCS_ENABLED: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Logging
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    LOG_JSON: bool = False

    # Database: DATABASE_URL, if set, overrides the individual DB_* parts
    DATABASE_URL: str | None = None
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: SecretStr = SecretStr("")
    DB_NAME: str = "taskmon"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE_SECONDS: int = 1800
    DB_ECHO: bool = False

    # Auth
    JWT_SECRET_KEY: SecretStr = Field(min_length=32)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    # OTP: hardcoded until an SMS provider is integrated
    STATIC_OTP: str = "1234"
    DEFAULT_COUNTRY_CODE: str = "91"

    # Groq LLM (server-side only; never sent to the frontend)
    GROQ_API_KEY: SecretStr = SecretStr("")
    GROQ_MODEL: str = "openai/gpt-oss-120b"
    GROQ_TIMEOUT_SECONDS: float = 20
    GROQ_MAX_RETRIES: int = 2  # the SDK retries timeouts, 429s and 5xx itself
    # gpt-oss models think before answering; "low" keeps that short (fewer tokens, faster). Empty = model default.
    GROQ_REASONING_EFFORT: str = "low"

    # Chat engine
    CHAT_DEBUG: bool = False  # log every step at INFO and return the steps in the chat response
    PENDING_ACTION_MINUTES: int = 15
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"

    # Push notifications (reminder worker): path to the Firebase Admin SDK service-account JSON.
    # Mounted into the worker container at run time; never committed or baked into the image.
    FIREBASE_CREDENTIALS_FILE: str = ""
    WORKER_INTERVAL_SECONDS: int = 30  # how often the worker looks for due reminders

    # CORS: comma-separated list of allowed frontend origins
    CORS_ORIGINS: str = "http://localhost:5173"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def database_url(self) -> URL:
        if self.DATABASE_URL:
            return make_url(self.DATABASE_URL)
        # URL.create escapes special characters in the password safely
        return URL.create(
            drivername="mysql+pymysql",
            username=self.DB_USER,
            password=self.DB_PASSWORD.get_secret_value(),
            host=self.DB_HOST,
            port=self.DB_PORT,
            database=self.DB_NAME,
            query={"charset": "utf8mb4"},
        )

    @model_validator(mode="after")
    def _check_production_safety(self) -> "Settings":
        if self.is_production:
            if self.DEBUG:
                raise ValueError("DEBUG must be false in production")
            if "*" in self.cors_origins:
                raise ValueError("CORS_ORIGINS must not contain '*' in production")
            # Secrets must come from the server's environment, never the .env.example placeholders
            if self.JWT_SECRET_KEY.get_secret_value().startswith("change-me"):
                raise ValueError("JWT_SECRET_KEY is still the .env.example placeholder; set a real secret")
            if not self.DATABASE_URL and self.DB_PASSWORD.get_secret_value() in ("", "change-me"):
                raise ValueError("DB_PASSWORD (or DATABASE_URL) must be set in production")
            if not self.GROQ_API_KEY.get_secret_value():
                raise ValueError("GROQ_API_KEY must be set in production")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # values come from env / .env


settings = get_settings()
