"""One Groq call per message: message type, intents and extracted fields, validated with Pydantic."""

import json
import logging
from typing import Any

from pydantic import ValidationError

from app.ai.groq_client import chat_completion
from app.ai.intent_catalogue import INTENTS
from app.ai.prompts import build_classifier_messages
from app.ai.schemas import ClassifierResult
from app.core.exceptions import AIServiceError

logger = logging.getLogger(__name__)

ATTEMPTS = 2  # one retry when Groq's JSON is unreadable or doesn't match the schema


def parse_result(raw: str) -> ClassifierResult:
    """Raw Groq text → validated result. Raises ValueError / ValidationError if unusable."""
    result = ClassifierResult.model_validate(json.loads(raw))

    unknown = [op.intent for op in result.operations if op.intent not in INTENTS]
    if unknown:
        logger.warning("Dropping unsupported intents from Groq: %s", unknown)
        result.operations = [op for op in result.operations if op.intent in INTENTS]
        if not result.operations and result.type in ("ACTION", "QUERY"):
            result.type = "FALLBACK"
            result.response = (
                result.response
                or "Sorry, I can't do that yet. I can help with reminders, expenses and notes."
            )
    return result


async def classify(
    context: dict[str, Any], history: list[dict[str, str]], message: str
) -> tuple[ClassifierResult, str]:
    """Returns the validated result and Groq's raw text (for the debug trace)."""
    messages = build_classifier_messages(context, history, message)
    raw = ""
    for attempt in range(1, ATTEMPTS + 1):
        raw = await chat_completion(messages)
        logger.debug("Groq raw reply (attempt %d): %s", attempt, raw)
        try:
            return parse_result(raw), raw
        except (ValueError, ValidationError) as exc:
            logger.warning(
                "Groq reply unusable (attempt %d/%d): %s | raw=%r", attempt, ATTEMPTS, exc, raw[:500]
            )
    raise AIServiceError("I couldn't understand that properly. Could you rephrase it?")
