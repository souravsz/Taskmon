"""Every operation TaskMon supports from chat. Sent to Groq in the system prompt and
used by FastAPI to validate what Groq returns."""

from dataclasses import dataclass

ACTION = "ACTION"
QUERY = "QUERY"


@dataclass(frozen=True)
class Intent:
    id: str
    module: str  # reminders | expenses | notes | system
    kind: str  # ACTION | QUERY
    description: str
    fields: tuple[str, ...] = ()
    required: tuple[str, ...] = ()
    examples: tuple[str, ...] = ()
    needs_target: bool = False  # acts on existing records the backend must find
    destructive: bool = False  # needs an explicit "yes" before running


# Formats Groq must use for each field
FIELD_FORMATS = {
    "title": "short text",
    "content": "note text",
    "append": "text to add to the end of the note",
    "date": "YYYY-MM-DD",
    "time": "HH:MM 24-hour",
    "recurrence": "daily | weekdays | weekly | monthly",
    "amount": "number in rupees",
    "category": "Food | Transport | Groceries | Bills | Shopping | Health | Entertainment | Misc",
    "description": "short text",
    "text": "words to search for",
    "date_from": "YYYY-MM-DD",
    "date_to": "YYYY-MM-DD",
    "month": "YYYY-MM",
    "compare_month": "YYYY-MM",
    "module": "reminders | expenses | notes",
}

CATEGORIES = ("Food", "Transport", "Groceries", "Bills", "Shopping", "Health", "Entertainment", "Misc")
RECURRENCES = ("daily", "weekdays", "weekly", "monthly")

# Asked when a required field is missing
QUESTIONS = {
    "title": "What should I call it?",
    "content": "What should the note say?",
    "date": "Which date?",
    "time": "When should I remind you?",
    "recurrence": "How often should it repeat: daily, weekdays, weekly or monthly?",
    "amount": "How much was it?",
    "text": "What should I search for?",
}

INTENTS: dict[str, Intent] = {
    i.id: i
    for i in (
        # ---------- Reminders ----------
        Intent("create_reminder", "reminders", ACTION, "One-time reminder (date defaults to today)",
               ("title", "date", "time"), ("title", "time"),
               ("Remind me to call Rahul tomorrow at 8 PM",)),
        Intent("create_recurring_reminder", "reminders", ACTION, "Repeating reminder",
               ("title", "time", "recurrence", "date"), ("title", "time", "recurrence"),
               ("Remind me to exercise every morning",)),
        Intent("update_reminder", "reminders", ACTION, "Change a reminder's title, date or time",
               ("title", "date", "time"), (), ("Change Rahul's reminder to 9 PM",), needs_target=True),
        Intent("complete_reminder", "reminders", ACTION, "Mark a reminder as done",
               (), (), ("Mark my call reminder as completed",), needs_target=True),
        Intent("cancel_reminder", "reminders", ACTION, "Stop a reminder from firing (it is kept, not deleted)",
               (), (), ("Cancel my 8 PM reminder",), needs_target=True),
        Intent("delete_reminder", "reminders", ACTION, "Permanently delete one or all reminders",
               (), (), ("Delete my dentist reminder",), needs_target=True, destructive=True),
        Intent("list_reminders", "reminders", QUERY, "List open reminders, optionally in a date range",
               ("date_from", "date_to"), (), ("Show my reminders for tomorrow",)),
        Intent("search_reminders", "reminders", QUERY, "Find reminders by words in the title",
               ("text",), ("text",), ("Do I have a reminder about the dentist?",)),
        # ---------- Expenses ----------
        Intent("create_expense", "expenses", ACTION, "Log money spent (date defaults to today)",
               ("amount", "category", "description", "date"), ("amount",),
               ("I spent ₹350 on food today",)),
        Intent("update_expense", "expenses", ACTION, "Change an expense",
               ("amount", "category", "description", "date"), (),
               ("Change yesterday's food expense to ₹400",), needs_target=True),
        Intent("delete_expense", "expenses", ACTION, "Delete one or all expenses",
               (), (), ("Delete my last expense",), needs_target=True, destructive=True),
        Intent("list_expenses", "expenses", QUERY, "List expenses, optionally by date range or category",
               ("date_from", "date_to", "category"), (), ("Show my expenses today",)),
        Intent("search_expenses", "expenses", QUERY, "Find expenses by words in the description or category",
               ("text",), ("text",), ("Find my Uber expenses",)),
        Intent("get_daily_expenses", "expenses", QUERY, "Total spent on one day (defaults to today)",
               ("date",), (), ("How much did I spend today?",)),
        Intent("get_monthly_expenses", "expenses", QUERY, "Total spent in a month (defaults to this month)",
               ("month",), (), ("How much did I spend this month?",)),
        Intent("get_expense_summary", "expenses", QUERY, "Total and category breakdown for a date range",
               ("date_from", "date_to", "category"), (), ("Summarise my spending this week",)),
        Intent("get_expense_comparison", "expenses", QUERY,
               "Compare two months (defaults: this month vs last month)",
               ("month", "compare_month"), (), ("Compare this month with last month",)),
        Intent("get_expense_insights", "expenses", QUERY, "Where the money goes in a month, by category",
               ("month",), (), ("Where am I spending the most?",)),
        # ---------- Notes ----------
        Intent("create_note", "notes", ACTION, "Save a note", ("title", "content"), ("title",),
               ("Save a note about my FastAPI project",)),
        Intent("update_note", "notes", ACTION, "Rename a note, replace its text, or add text to it",
               ("title", "content", "append"), (), ("Add Docker information to that note",),
               needs_target=True),
        Intent("delete_note", "notes", ACTION, "Delete one or all notes", (), (), ("Delete my old project note",),
               needs_target=True, destructive=True),
        Intent("search_notes", "notes", QUERY, "Find notes by words in title or content", ("text",), ("text",),
               ("Find my AWS-related notes",)),
        Intent("list_notes", "notes", QUERY, "List notes", (), (), ("Show all my notes",)),
        Intent("get_note_details", "notes", QUERY, "Show the full text of the matching note", ("text",),
               ("text",), ("What did I save about Docker?",)),
        # ---------- Undo (any module) ----------
        Intent("undo_last_action", "system", ACTION, "Reverse the most recent change, optionally of one module",
               ("module",), (), ("Undo the last expense entry",)),
    )
}  # fmt: skip


def render_catalogue() -> str:
    """Compact list for the system prompt: field formats once, then one line per intent."""
    lines = ["Field formats: " + "; ".join(f"{f} = {fmt}" for f, fmt in FIELD_FORMATS.items()), ""]
    for i in INTENTS.values():
        fields = ", ".join(f"{f}{'*' if f in i.required else ''}" for f in i.fields)
        target = " [needs target]" if i.needs_target else ""
        lines.append(
            f"- {i.id} ({i.kind}){target}: {i.description}."
            + (f" Fields: {fields}." if fields else "")
            + f' e.g. "{i.examples[0]}"'
        )
    return "\n".join(lines)
