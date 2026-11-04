from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.schemas.pagination import Page


class ExpenseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # Serialised as a string (e.g. "450.00") to avoid float rounding
    amount: Decimal
    category: str
    description: str | None
    spent_at: datetime


class ExpensePage(Page[ExpenseRead]):
    total_amount: Decimal
