import json
import logging
import logging.config
from contextvars import ContextVar
from datetime import UTC, datetime

from app.core.config import settings

# Set per request by RequestContextMiddleware; "-" outside a request.
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True


class JsonFormatter(logging.Formatter):
    """One JSON object per line, for log shippers (CloudWatch, Loki, ELK…)."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "request_id": getattr(record, "request_id", "-"),
            "message": record.getMessage(),
        }
        if record.exc_info:
            entry["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


def configure_logging() -> None:
    formatter = (
        {"()": JsonFormatter}
        if settings.LOG_JSON
        else {"format": "%(asctime)s %(levelname)-8s %(name)s [%(request_id)s] %(message)s"}
    )
    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "filters": {"request_id": {"()": RequestIdFilter}},
            "formatters": {"default": formatter},
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "filters": ["request_id"],
                }
            },
            "root": {"handlers": ["console"], "level": settings.LOG_LEVEL},
            "loggers": {
                # Our middleware writes access logs (with request id and duration) instead.
                "uvicorn.access": {"level": "WARNING"},
                "sqlalchemy.engine": {"level": "INFO" if settings.DB_ECHO else "WARNING"},
            },
        }
    )
