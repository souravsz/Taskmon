"""CONVERSATION, CLARIFICATION and FALLBACK: no data is touched.

CONVERSATION (greetings, questions about TaskMon) and CLARIFICATION show Groq's reply.
FALLBACK (anything unrelated) always shows the same fixed reply; Groq's text is ignored.
"""

from app.ai.schemas import ClassifierResult
from app.conversation.context import Turn

FALLBACK_TEXT = "Sorry, I can only help with your reminders, expenses and notes."

DEFAULTS = {
    "CONVERSATION": "I'm here! How can I help?",
    "CLARIFICATION": "Could you tell me a bit more about what you'd like me to do?",
}


def reply(turn: Turn, result: ClassifierResult) -> None:
    if result.type == "FALLBACK":
        text = FALLBACK_TEXT
    else:
        text = (result.response or "").strip() or DEFAULTS.get(result.type, DEFAULTS["CLARIFICATION"])
    turn.step("conversation.reply", type=result.type)
    turn.say(text)
