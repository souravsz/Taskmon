import logging
import time
from functools import lru_cache

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


async def chat_completion(messages: list[dict[str, str]], json_mode: bool = True) -> str:
    """Send `messages` to Groq and return the reply text. Raises AIServiceError on any failure."""
    if not settings.GROQ_API_KEY.get_secret_value():
        raise AIServiceError("GROQ_API_KEY is not set in backend/.env")

    extra = {"reasoning_effort": settings.GROQ_REASONING_EFFORT} if settings.GROQ_REASONING_EFFORT else {}
    started = time.perf_counter()
    try:
        completion = await get_client().chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=messages,  # type: ignore[arg-type]
            response_format={"type": "json_object"} if json_mode else {"type": "text"},
            temperature=0 if json_mode else 0.4,
            **extra,  # type: ignore[arg-type]
        )
    except groq.RateLimitError as exc:
        logger.warning("Groq rate limit: %s", exc)
        raise AIServiceError(
            "I'm getting a lot of requests right now. Please try again in a minute."
        ) from exc
    except groq.APITimeoutError as exc:
        logger.warning("Groq timed out after %.1fs", time.perf_counter() - started)
        raise AIServiceError("That took too long to think about. Please try again.") from exc
    except groq.APIConnectionError as exc:
        logger.warning("Groq unreachable: %s", exc)
        raise AIServiceError(
            "I can't reach my language service right now. Please try again shortly."
        ) from exc
    except groq.APIStatusError as exc:
        logger.warning("Groq returned %s: %s", exc.status_code, exc)
        raise AIServiceError() from exc

    text = completion.choices[0].message.content or ""
    usage = completion.usage
    logger.info(
        "Groq %s replied in %.2fs (tokens in=%s out=%s)",
        settings.GROQ_MODEL,
        time.perf_counter() - started,
        usage.prompt_tokens if usage else "?",
        usage.completion_tokens if usage else "?",
    )
    return text
