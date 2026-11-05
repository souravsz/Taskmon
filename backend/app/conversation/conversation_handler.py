"""CONVERSATION, CLARIFICATION and FALLBACK: no data is touched, Groq's reply is shown as is."""

from app.ai.schemas import ClassifierResult
from app.conversation.context import Turn

DEFAULTS = {
    "CONVERSATION": "I'm here! How can I help?",
    "CLARIFICATION": "Could you tell me a bit more about what you'd like me to do?",
    "FALLBACK": "Sorry, I can't do that. I can help with reminders, expenses and notes.",
}


def reply(turn: Turn, result: ClassifierResult) -> None:
    text = (result.response or "").strip() or DEFAULTS.get(result.type, DEFAULTS["CLARIFICATION"])
    turn.step("conversation.reply", type=result.type)
    turn.say(text)
