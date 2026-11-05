"""Bank SMS → expense. Only Federal Bank debit alerts, in exactly this format:

Debited Rs 50.00 from a/c X9844 on 04Nov26 12:57 via UPI to SAFIYA HASSA. Ref 630830086298.
Bal Rs 407.64. Not you? Call 18004251199 -Federal Bank
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.response_generator import inr
from app.conversation.context import local_now
from app.models.expense import Expense
from app.models.user import User
from app.services import device_service, expense_service, push_service

logger = logging.getLogger(__name__)

FEDERAL_BANK_DEBIT = re.compile(
    r"Debited Rs\.?\s*(?P<amount>[\d,]+(?:\.\d{1,2})?)"
    r" from a/c (?P<account>\w+)"
    r" on (?P<date>\d{2}[A-Za-z]{3}\d{2}) (?P<time>\d{1,2}:\d{2})"
    r" via (?P<method>[A-Za-z]+)"
    r" to (?P<recipient>.+?)\."
    r"\s*Ref (?P<reference>\w+)\."
    r".*-\s*Federal Bank",
    re.DOTALL,
)

BANK = "Federal Bank"
CATEGORY = "Misc"  # the SMS doesn't say what the money was for; the user can change it in chat


@dataclass
class BankDebit:
    amount: Decimal
    spent_at: datetime  # the bank's date and time (the user's local time)
    method: str  # UPI
    recipient: str
    account: str  # X9844
    reference: str


def parse(text: str) -> BankDebit | None:
    """The debit in a Federal Bank SMS, or None if the text isn't one."""
    m = FEDERAL_BANK_DEBIT.search(" ".join(text.split()))  # SMS line breaks → spaces
    if not m:
        return None
    try:
        spent_at = datetime.strptime(f"{m['date']} {m['time']}", "%d%b%y %H:%M")
    except ValueError:
        return None
    return BankDebit(
        amount=Decimal(m["amount"].replace(",", "")),
        spent_at=spent_at,
        method=m["method"].upper(),
        recipient=m["recipient"].strip(),
        account=m["account"],
        reference=m["reference"],
    )


@dataclass
class SmsResult:
    recorded: bool
    reason: str
    expense: Expense | None = None
    spent_today: Decimal | None = None
    daily_budget: Decimal | None = None
    over_budget: bool = False


def record(db: Session, user: User, text: str) -> SmsResult:
    """Saves the debit as an expense (once per bank reference) and warns if the day's budget is passed."""
    debit = parse(text)
    if debit is None:
        logger.info("Bank SMS user=%s not a Federal Bank debit: %r", user.id, text[:80])
        return SmsResult(recorded=False, reason="not_a_federal_bank_debit")

    already = db.scalar(
        select(Expense).where(Expense.user_id == user.id, Expense.reference == debit.reference)
    )
    if already is not None:
        logger.info(
            "Bank SMS user=%s ref=%s already recorded as expense=%s", user.id, debit.reference, already.id
        )
        return SmsResult(recorded=False, reason="already_recorded", expense=already)

    description = f"{debit.method} to {debit.recipient} · {BANK} {debit.account}"
    try:
        expense = expense_service.create(db, user.id, debit.amount, CATEGORY, description, debit.spent_at)
        expense.reference = debit.reference
        db.flush()
    except IntegrityError:
        # The same SMS sent twice at once (app-open sync and the live SMS task): the other one saved it
        db.rollback()
        logger.info("Bank SMS user=%s ref=%s saved by a parallel request", user.id, debit.reference)
        return SmsResult(recorded=False, reason="already_recorded")

    day = datetime.combine(debit.spent_at.date(), time())
    spent_today, _ = expense_service.total_in_range(db, user.id, day, day + timedelta(days=1))
    budget = user.expense_limit
    over = budget is not None and spent_today > budget
    db.commit()
    # Messages caught up after being offline can be days old: only a payment made today warns
    is_today = debit.spent_at.date() == local_now(user).date()
    logger.info(
        "Bank SMS user=%s ref=%s recorded expense=%s %s to %r | day total %s, budget %s, over=%s, today=%s",
        user.id,
        debit.reference,
        expense.id,
        debit.amount,
        debit.recipient,
        spent_today,
        budget,
        over,
        is_today,
    )
    if over and is_today and budget is not None:
        warn_over_budget(db, user, debit, spent_today, budget)
    return SmsResult(
        recorded=True,
        reason="recorded",
        expense=expense,
        spent_today=spent_today,
        daily_budget=budget,
        over_budget=over,
    )


def warn_over_budget(db: Session, user: User, debit: BankDebit, spent: Decimal, budget: Decimal) -> None:
    """Push to every phone of the user. Never fails the request: the expense is already saved."""
    title = "Daily budget exceeded"
    text = f"You've spent {inr(spent)} today, over your {inr(budget)} budget. Last: {inr(debit.amount)} to {debit.recipient}."
    data = {"type": "budget", "spent": str(spent), "budget": str(budget)}
    try:
        tokens = device_service.tokens_for_user(db, user.id)
        results = [push_service.send(token, title, text, data) for token in tokens]
    except Exception:
        logger.exception("Budget warning user=%s could not be sent", user.id)
        return
    dead = [token for token, result in zip(tokens, results, strict=True) if result == "dead"]
    if dead:
        device_service.delete_tokens(db, dead)
        db.commit()
    logger.info("Budget warning user=%s phones=%d sent=%d", user.id, len(tokens), results.count("sent"))
