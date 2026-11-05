"""QUERY intents: read from MySQL and calculate in Python (Decimal). Groq never supplies figures."""

import calendar
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from typing import Any

from app.ai.intent_catalogue import Intent
from app.ai.response_generator import day_label, inr, insights_tip, pct_change, record_card
from app.conversation.context import Turn
from app.services import expense_service, note_service, reminder_service

LIST_LIMIT = 10


def day_start(day: date) -> datetime:
    return datetime.combine(day, time())


def on_day(day: date, today: date) -> str:
    """'today', 'yesterday', 'on Mon 3 Nov'"""
    label = day_label(day, today)
    return label.lower() if label in ("Today", "Yesterday", "Tomorrow") else f"on {label}"


def date_range(values: dict[str, Any], today: date) -> tuple[datetime | None, datetime | None, str]:
    """(start, end exclusive, ' for tomorrow' style label) from date_from / date_to."""
    first, last = values.get("date_from"), values.get("date_to")
    start = day_start(first) if first else None
    end = day_start(last) + timedelta(days=1) if last else None
    if first and last and first == last:
        day = day_label(first, today)
        label = f" for {day.lower() if day in ('Today', 'Yesterday', 'Tomorrow') else day}"
    elif first and last:
        label = f" from {day_label(first, today)} to {day_label(last, today)}"
    elif first:
        label = f" from {day_label(first, today)}"
    elif last:
        label = f" until {day_label(last, today)}"
    else:
        label = ""
    return start, end, label


def month_bounds(first: date) -> tuple[datetime, datetime, str]:
    days = calendar.monthrange(first.year, first.month)[1]
    start = day_start(first.replace(day=1))
    return start, start + timedelta(days=days), first.strftime("%B %Y")


def previous_month(first: date) -> date:
    return (first.replace(day=1) - timedelta(days=1)).replace(day=1)


def count_text(shown: int, total: int, word: str = "") -> str:
    return f"{total}{' ' + word if word else ''}" if shown >= total else f"{shown} of {total}"


def category_rows(rows: list[tuple[str, Decimal, int]], total: Decimal) -> list[dict[str, Any]]:
    """Breakdown rows for a card (not numbered: they aren't records you can act on)."""
    return [
        {
            "entity": "category",
            "id": 0,
            "title": category,
            "subtitle": f"{inr(amount)} · {(amount / total * 100).quantize(Decimal('1')) if total else 0}%",
            "detail": None,
        }
        for category, amount, _ in rows
    ]


async def run_query(turn: Turn, intent: Intent, values: dict[str, Any]) -> None:
    db, uid, now = turn.db, turn.user.id, turn.now
    today = now.date()
    cards = lambda rows, full=False: [record_card(r, now, full) for r in rows]  # noqa: E731

    # ---------- reminders
    if intent.id == "list_reminders":
        start, end, label = date_range(values, today)
        rows, total = reminder_service.list_open(db, uid, start, end, LIST_LIMIT)
        turn.step("query.result", intent=intent.id, shown=len(rows), total=total)
        if not rows:
            turn.say(f"You have no open reminders{label}.")
            return
        turn.say(
            f"Here are your reminders{label}.", cards(rows), "Reminders", count_text(len(rows), total, "open")
        )

    elif intent.id == "search_reminders":
        rows = reminder_service.search(db, uid, values["text"], LIST_LIMIT)
        turn.step("query.result", intent=intent.id, found=len(rows))
        if not rows:
            turn.say(f"No reminders match “{values['text']}”.")
            return
        turn.say(f"Reminders matching “{values['text']}”:", cards(rows), "Reminders", f"{len(rows)} found")

    # ---------- expenses
    elif intent.id == "list_expenses":
        start, end, label = date_range(values, today)
        category = values.get("category")
        rows, count = expense_service.list_in_range(db, uid, start, end, category, LIST_LIMIT)
        total, _ = expense_service.total_in_range(db, uid, start, end, category)
        turn.step("query.result", intent=intent.id, shown=len(rows), count=count, total=str(total))
        what = f"{category} expenses" if category else "expenses"
        if not rows:
            turn.say(f"You have no {what}{label}.")
            return
        turn.say(f"Here are your {what}{label}.", cards(rows), "Expenses", f"{inr(total)} total")

    elif intent.id == "search_expenses":
        rows = expense_service.search(db, uid, values["text"], LIST_LIMIT)
        turn.step("query.result", intent=intent.id, found=len(rows))
        if not rows:
            turn.say(f"No expenses match “{values['text']}”.")
            return
        total = sum((r.amount for r in rows), Decimal(0))
        turn.say(f"Expenses matching “{values['text']}”:", cards(rows), "Expenses", f"{inr(total)} total")

    elif intent.id == "get_daily_expenses":
        day = values.get("date", today)
        start = day_start(day)
        total, count = expense_service.total_in_range(db, uid, start, start + timedelta(days=1))
        rows, _ = expense_service.list_in_range(db, uid, start, start + timedelta(days=1), limit=LIST_LIMIT)
        turn.step("query.result", intent=intent.id, day=str(day), total=str(total), count=count)
        when = on_day(day, today)
        if count == 0:
            turn.say(f"You haven't logged any spending {when}.")
            return
        turn.say(
            f"You spent {inr(total)} {when} across {count} expense{'s' if count != 1 else ''}.",
            cards(rows),
            "Expenses",
            f"{inr(total)} total",
        )

    elif intent.id == "get_monthly_expenses":
        start, end, label = month_bounds(values.get("month", today.replace(day=1)))
        total, count = expense_service.total_in_range(db, uid, start, end)
        by_category = expense_service.totals_by_category(db, uid, start, end)
        turn.step("query.result", intent=intent.id, month=label, total=str(total), count=count)
        if count == 0:
            turn.say(f"You haven't logged any spending in {label}.")
            return
        turn.say(
            f"You spent {inr(total)} in {label} across {count} expense{'s' if count != 1 else ''}.",
            category_rows(by_category, total),
            "By category",
            inr(total),
            numbered=False,
        )

    elif intent.id == "get_expense_summary":
        start, end, label = date_range(values, today)
        if start is None and end is None:
            start, end, month_label = month_bounds(today.replace(day=1))
            label = f" in {month_label}"
        category = values.get("category")
        total, count = expense_service.total_in_range(db, uid, start, end, category)
        turn.step("query.result", intent=intent.id, total=str(total), count=count)
        if count == 0:
            turn.say(f"No spending{' on ' + category if category else ''}{label}.")
            return
        if category:
            turn.say(
                f"You spent {inr(total)} on {category}{label} across {count} expense{'s' if count != 1 else ''}."
            )
            return
        by_category = expense_service.totals_by_category(db, uid, start, end)
        turn.say(
            f"You spent {inr(total)}{label} across {count} expense{'s' if count != 1 else ''}.",
            category_rows(by_category, total),
            "By category",
            inr(total),
            numbered=False,
        )

    elif intent.id == "get_expense_comparison":
        month = values.get("month", today.replace(day=1))
        other = values.get("compare_month", previous_month(month))
        a_start, a_end, a_label = month_bounds(month)
        b_start, b_end, b_label = month_bounds(other)
        a_total, _ = expense_service.total_in_range(db, uid, a_start, a_end)
        b_total, _ = expense_service.total_in_range(db, uid, b_start, b_end)
        diff = a_total - b_total
        pct = pct_change(a_total, b_total)
        turn.step(
            "query.result", intent=intent.id, a=str(a_total), b=str(b_total), diff=str(diff), pct=str(pct)
        )
        so_far = " so far" if month == today.replace(day=1) else ""
        if diff == 0:
            change = "That's exactly the same."
        else:
            direction = "more" if diff > 0 else "less"
            change = f"That's {inr(abs(diff))} {direction}" + (f" ({pct:+}%)." if pct is not None else ".")
        turn.say(
            f"{a_label}{so_far}: {inr(a_total)}. {b_label}: {inr(b_total)}. {change}",
            [
                {"entity": "month", "id": 0, "title": a_label, "subtitle": inr(a_total), "detail": None},
                {"entity": "month", "id": 0, "title": b_label, "subtitle": inr(b_total), "detail": None},
            ],
            "Comparison",
            f"{'+' if diff > 0 else ''}{inr(diff)}",
            numbered=False,
        )

    elif intent.id == "get_expense_insights":
        month = values.get("month", today.replace(day=1))
        start, end, label = month_bounds(month)
        total, count = expense_service.total_in_range(db, uid, start, end)
        if count == 0:
            turn.say(f"You haven't logged any spending in {label}, so there's nothing to analyse yet.")
            return
        by_category = expense_service.totals_by_category(db, uid, start, end)
        biggest = expense_service.largest_in_range(db, uid, start, end)
        days = (today - month).days + 1 if month == today.replace(day=1) else (end - start).days
        per_day = (total / days).quantize(Decimal("0.01"))
        prev_start, prev_end, prev_label = month_bounds(previous_month(month))
        prev_total, _ = expense_service.total_in_range(db, uid, prev_start, prev_end)
        top_category, top_amount, _ = by_category[0]
        top_share = (top_amount / total * 100).quantize(Decimal("1"))
        figures = {
            "month": label,
            "total": inr(total),
            "expenses": count,
            "top_category": top_category,
            "top_category_amount": inr(top_amount),
            "top_category_share_percent": str(top_share),
            "biggest_expense": f"{inr(biggest.amount)} on {biggest.description or biggest.category}"
            if biggest
            else None,
            "average_per_day": inr(per_day),
            "previous_month": prev_label,
            "previous_month_total": inr(prev_total),
        }
        turn.step("query.result", intent=intent.id, figures=figures)
        lines = [
            f"In {label} you spent {inr(total)}. Most of it went on {top_category}: {inr(top_amount)} ({top_share}%).",
            f"That's about {inr(per_day)} a day.",
        ]
        if biggest:
            lines.append(f"Your biggest single expense was {figures['biggest_expense']}.")
        calls: list[dict[str, Any]] = []
        tip = await insights_tip(figures, calls)
        turn.groq_steps(calls, "insights tip")
        if tip:
            lines.append(tip)
        turn.say(
            " ".join(lines), category_rows(by_category, total), "Where it went", inr(total), numbered=False
        )

    # ---------- notes
    elif intent.id == "list_notes":
        rows, total = note_service.list_recent(db, uid, LIST_LIMIT)
        turn.step("query.result", intent=intent.id, shown=len(rows), total=total)
        if not rows:
            turn.say("You don't have any notes yet.")
            return
        turn.say("Here are your notes.", cards(rows), "Notes", count_text(len(rows), total, "notes"))

    elif intent.id == "search_notes":
        rows = note_service.search(db, uid, values["text"], LIST_LIMIT)
        turn.step("query.result", intent=intent.id, found=len(rows))
        if not rows:
            turn.say(f"I couldn't find any notes about “{values['text']}”.")
            return
        turn.say(f"Notes matching “{values['text']}”:", cards(rows), "Notes", f"{len(rows)} found")

    elif intent.id == "get_note_details":
        rows = note_service.search(db, uid, values["text"], 3)
        turn.step("query.result", intent=intent.id, found=len(rows))
        if not rows:
            turn.say(f"I couldn't find anything about “{values['text']}” in your notes.")
            return
        turn.say(
            f"Here's what you saved about “{values['text']}”:",
            cards(rows, full=True),
            "Notes",
            f"{len(rows)} found",
        )
