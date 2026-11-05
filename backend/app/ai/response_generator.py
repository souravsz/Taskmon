"""Turns backend results into reply text and card rows. Figures always come from the database;
Groq only adds a short advice sentence for insights, and is told to use only the figures given."""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from app.ai.groq_client import chat_completion
from app.ai.prompts import build_insights_messages
from app.core.exceptions import AIServiceError
from app.models.expense import Expense
from app.models.note import Note
from app.models.notification_task import NotificationTask

logger = logging.getLogger(__name__)

Record = NotificationTask | Expense | Note


def inr(amount: Decimal) -> str:
    """Decimal('123456.5') → '₹1,23,456.50'; whole rupees drop the paise: '₹350'."""
    amount = Decimal(amount).quantize(Decimal("0.01"))
    sign = "-" if amount < 0 else ""
    rupees, paise = f"{abs(amount):.2f}".split(".")
    # Indian grouping: last 3 digits, then pairs
    head, tail = rupees[:-3], rupees[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    grouped = ",".join([*groups, tail])
    return f"{sign}₹{grouped}" + ("" if paise == "00" else f".{paise}")


def day_label(day: date, today: date) -> str:
    diff = (day - today).days
    if diff == 0:
        return "Today"
    if diff == 1:
        return "Tomorrow"
    if diff == -1:
        return "Yesterday"
    if 1 < diff < 7:
        return day.strftime("%A")
    return f"{day.strftime('%a')} {day.day} {day.strftime('%b')}" + (
        "" if day.year == today.year else f" {day.year}"
    )


def clock(at: datetime) -> str:
    """20:00 → '8:00 PM'."""
    return f"{at.hour % 12 or 12}:{at.minute:02d} {'AM' if at.hour < 12 else 'PM'}"


def when(at: datetime, now: datetime) -> str:
    return f"{day_label(at.date(), now.date())} · {clock(at)}"


def entity_of(record: Record) -> str:
    if isinstance(record, NotificationTask):
        return "reminder"
    return "expense" if isinstance(record, Expense) else "note"


def record_card(record: Record, now: datetime, full: bool = False) -> dict[str, Any]:
    """One card row: {"entity", "id", "title", "subtitle", "detail"}. `full` adds a note's whole text."""
    if isinstance(record, NotificationTask):
        subtitle = when(record.notify_at, now)
        if record.recurrence:
            subtitle += f" · repeats {record.recurrence}"
        if record.is_completed:
            subtitle += " · done"
        elif record.is_cancelled:
            subtitle += " · cancelled"
        title, detail = record.title, None
    elif isinstance(record, Expense):
        title = record.description or record.category
        subtitle = (
            f"{inr(record.amount)} · {record.category} · {day_label(record.spent_at.date(), now.date())}"
        )
        detail = None
    else:
        content = record.content or ""
        title = record.title
        subtitle = (content[:80] + "…") if len(content) > 80 else (content or "Empty note")
        detail = content if full else None
    return {
        "entity": entity_of(record),
        "id": record.id,
        "title": title,
        "subtitle": subtitle,
        "detail": detail,
    }


def describe(record: Record, now: datetime) -> str:
    """Short inline description used in sentences: '“Call Rahul” (Tomorrow · 8:00 PM)'."""
    card = record_card(record, now)
    return f"“{card['title']}” ({card['subtitle']})"


def pct_change(current: Decimal, previous: Decimal) -> Decimal | None:
    if previous == 0:
        return None
    return ((current - previous) / previous * 100).quantize(Decimal("0.1"))


async def insights_tip(figures: dict[str, Any], calls: list[dict[str, Any]]) -> str | None:
    """A sentence of advice written by Groq from our figures. None if Groq is unavailable."""
    try:
        tip = await chat_completion(build_insights_messages(figures), json_mode=False, calls=calls)
    except AIServiceError as exc:
        logger.info("Skipping insights tip: %s", exc)
        return None
    return tip.strip() or None
