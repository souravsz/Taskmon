from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.schemas.pagination import PageParams
from app.services.pagination import paginate


def list_for_user(db: Session, user_id: int, params: PageParams) -> tuple[Sequence[Expense], int]:
    """Most recent spending first."""
    query = (
        select(Expense).where(Expense.user_id == user_id).order_by(Expense.spent_at.desc(), Expense.id.desc())
    )
    return paginate(db, query, params)


def total_for_user(db: Session, user_id: int) -> Decimal:
    total = db.scalar(select(func.sum(Expense.amount)).where(Expense.user_id == user_id))
    return Decimal(total or 0).quantize(Decimal("0.01"))
