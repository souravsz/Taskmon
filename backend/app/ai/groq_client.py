import logging
import time
from functools import lru_cache
from typing import Any

import groq
from groq import AsyncGroq

from app.core.config import settings
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)


@lru_cache
def get_client() -> AsyncGroq:
    """One client for the whole app; it keeps its HTTP connection pool between requests."""
    return AsyncGroq(
        api_key=settings.GROQ_API_KEY.get_secret_value(),
        timeout=settings.GROQ_TIMEOUT_SECONDS,
        max_retries=settings.GROQ_MAX_RETRIES,
    )


async def chat_completion(
    messages: list[dict[str, str]], json_mode: bool = True, calls: list[dict[str, Any]] | None = None
) -> str:
    """Send `messages` to Groq and return the reply text. Raises AIServiceError on any failure.

    If `calls` is given, the exact request and Groq's reply (or the error) are appended to it for the
    debug trace: {"request", "response" | "error", "duration_ms", "tokens"}."""
    if not settings.GROQ_API_KEY.get_secret_value():
        raise AIServiceError("GROQ_API_KEY is not set in backend/.env")

    params: dict[str, Any] = {
        "model": settings.GROQ_MODEL,
        "temperature": 0 if json_mode else 0.4,
        "response_format": {"type": "json_object"} if json_mode else {"type": "text"},
    }
    if settings.GROQ_REASONING_EFFORT:
        params["reasoning_effort"] = settings.GROQ_REASONING_EFFORT
    started = time.perf_counter()
    record: dict[str, Any] = {"request": {**params, "messages": messages}, "sent_at": started}
    if calls is not None:
        calls.append(record)

    try:
        completion = await get_client().chat.completions.create(messages=messages, **params)  # type: ignore[arg-type]
    except groq.APIError as exc:
        record["duration_ms"] = round((time.perf_counter() - started) * 1000)
        record["error"] = f"{type(exc).__name__}: {exc}"
        logger.warning("Groq call failed after %sms: %s", record["duration_ms"], record["error"])
        # In JSON mode Groq rejects a plain-text reply with 400 json_validate_failed. That's an unusable
        # reply, not an outage: return "" so the caller handles it like unreadable JSON (retry, then FALLBACK).
        if isinstance(exc, groq.BadRequestError) and "json_validate_failed" in str(exc.body):
            return ""
        raise AIServiceError(_friendly(exc)) from exc

    text = completion.choices[0].message.content or ""
    usage = completion.usage
    record["duration_ms"] = round((time.perf_counter() - started) * 1000)
    record["response"] = text
    record["tokens"] = (
        {"prompt": usage.prompt_tokens, "completion": usage.completion_tokens, "total": usage.total_tokens}
        if usage
        else None
    )
    logger.info(
        "Groq %s replied in %sms (tokens %s)", settings.GROQ_MODEL, record["duration_ms"], record["tokens"]
    )
    return text


def _friendly(exc: groq.APIError) -> str:
    """What the user sees for each kind of Groq failure."""
    if isinstance(exc, groq.RateLimitError):
        return "I'm getting a lot of requests right now. Please try again in a minute."
    if isinstance(exc, groq.APITimeoutError):
        return "That took too long to think about. Please try again."
    if isinstance(exc, groq.APIConnectionError):
        return "I can't reach my language service right now. Please try again shortly."
    return AIServiceError.message
