from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Username = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9_]{3,30}$"),
    Field(description="3-30 characters: letters, numbers and underscore", examples=["john_doe"]),
]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mobile_number: str
    username: str | None
    # Stored as users.expense_limit; a bank SMS that takes the day's spending past it sends a warning push
    daily_budget: Decimal | None = Field(default=None, validation_alias="expense_limit")
    created_at: datetime


class UsernameUpdate(BaseModel):
    username: Username


class DailyBudgetUpdate(BaseModel):
    daily_budget: Decimal = Field(gt=0, le=10_000_000, decimal_places=2, examples=[500])
