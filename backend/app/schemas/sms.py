from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class BankSmsIn(BaseModel):
    """The full text of a bank SMS, forwarded by the phone as it arrives."""

    text: str = Field(min_length=1, max_length=1000)


class BankSmsResult(BaseModel):
    recorded: bool
    reason: str  # recorded | already_recorded | not_a_federal_bank_debit
    expense_id: int | None = None
    amount: Decimal | None = None
    spent_at: datetime | None = None
    description: str | None = None
    spent_today: Decimal | None = None
    daily_budget: Decimal | None = None
    over_budget: bool = False
