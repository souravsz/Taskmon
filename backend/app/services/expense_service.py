from collections.abc import Sequence
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from sqlalchemy import ColumnElement, Select, func, or_, select
from sqlalchemy.orm import Session

from app.models.expense import Expense
from app.schemas.pagination import PageParams
from app.services.pagination import paginate

CENTS = Decimal("0.01")


def money(value: object) -> Decimal:
    """SQL SUM can come back as Decimal, int, float or None; always return an exact 2-place Decimal."""
    return Decimal(str(value or 0)).quantize(CENTS)


def list_for_user(
    db: Session, user_id: int, params: PageParams, include_uncounted: bool = False
) -> tuple[Sequence[Expense], int]:
    """Most recent spending first. "Don't count" expenses only when asked for."""
    query = select(Expense).where(Expense.user_id == user_id)
    if not include_uncounted:
        query = query.where(Expense.counted.is_(True))
    return paginate(db, query.order_by(Expense.spent_at.desc(), Expense.id.desc()), params)


def total_for_user(db: Session, user_id: int) -> Decimal:
    total = db.scalar(
        select(func.sum(Expense.amount)).where(Expense.user_id == user_id, Expense.counted.is_(True))
    )
    return Decimal(total or 0).quantize(Decimal("0.01"))


def get_for_user(db: Session, user_id: int, expense_id: int) -> Expense | None:
    return db.scalar(select(Expense).where(Expense.id == expense_id, Expense.user_id == user_id))


def set_counted(db: Session, expense: Expense, counted: bool) -> None:
    """The "Don't count" / "Count" buttons: a not-counted expense is kept but left out of every total."""
    expense.counted = counted
    db.flush()


def _in_range(
    user_id: int,
    start: datetime | None,
    end: datetime | None,
    category: str | None = None,
    include_uncounted: bool = False,
) -> list[ColumnElement[bool]]:
    """Totals, the daily budget and lists leave out "Don't count" expenses unless include_uncounted."""
    conditions: list[ColumnElement[bool]] = [Expense.user_id == user_id]
    if not include_uncounted:
        conditions.append(Expense.counted.is_(True))
    if start:
        conditions.append(Expense.spent_at >= start)
    if end:
        conditions.append(Expense.spent_at < end)
    if category:
        conditions.append(Expense.category == category)
    return conditions


def _with_words(query: Select[tuple[Expense]], text: str | None) -> Select[tuple[Expense]]:
    for word in (text or "").split():
        query = query.where(or_(Expense.description.ilike(f"%{word}%"), Expense.category.ilike(f"%{word}%")))
    return query


def list_in_range(
    db: Session,
    user_id: int,
    start: datetime | None = None,
    end: datetime | None = None,
    category: str | None = None,
    limit: int = 10,
    include_uncounted: bool = False,
) -> tuple[list[Expense], int]:
    query = select(Expense).where(*_in_range(user_id, start, end, category, include_uncounted))
    rows, total = paginate(
        db, query.order_by(Expense.spent_at.desc(), Expense.id.desc()), PageParams(limit=limit, offset=0)
    )
    return list(rows), total


def uncounted_in_range(
    db: Session, user_id: int, start: datetime | None, end: datetime | None, category: str | None = None
) -> int:
    """How many "Don't count" expenses a counted-only list left out."""
    conditions = [
        *_in_range(user_id, start, end, category, include_uncounted=True),
        Expense.counted.is_(False),
    ]
    return int(db.scalar(select(func.count(Expense.id)).where(*conditions)) or 0)


def search(db: Session, user_id: int, text: str, limit: int = 10) -> list[Expense]:
    """Every match, counted or not (the card marks the ones that aren't)."""
    query = _with_words(select(Expense).where(Expense.user_id == user_id), text)
    return list(db.scalars(query.order_by(Expense.spent_at.desc(), Expense.id.desc()).limit(limit)))


def find(
    db: Session, user_id: int, text: str | None = None, day: date | None = None, limit: int = 20
) -> list[Expense]:
    """Expenses matching every given criterion (used to find the target of update / delete)."""
    query = _with_words(select(Expense).where(Expense.user_id == user_id), text)
    if day:
        start = datetime.combine(day, time())
        query = query.where(Expense.spent_at >= start, Expense.spent_at < start + timedelta(days=1))
    return list(db.scalars(query.order_by(Expense.spent_at.desc(), Expense.id.desc()).limit(limit)))


def latest(db: Session, user_id: int) -> Expense | None:
    return db.scalar(select(Expense).where(Expense.user_id == user_id).order_by(Expense.id.desc()).limit(1))


def total_in_range(
    db: Session, user_id: int, start: datetime | None, end: datetime | None, category: str | None = None
) -> tuple[Decimal, int]:
    """(total spent, number of expenses) in [start, end)."""
    total, count = db.execute(
        select(func.sum(Expense.amount), func.count(Expense.id)).where(
            *_in_range(user_id, start, end, category)
        )
    ).one()
    return money(total), int(count)


def totals_by_category(
    db: Session, user_id: int, start: datetime | None, end: datetime | None
) -> list[tuple[str, Decimal, int]]:
    """[(category, total, count)] biggest first."""
    rows = db.execute(
        select(Expense.category, func.sum(Expense.amount), func.count(Expense.id))
        .where(*_in_range(user_id, start, end))
        .group_by(Expense.category)
    ).all()
    return sorted(((c, money(t), int(n)) for c, t, n in rows), key=lambda r: r[1], reverse=True)


def largest_in_range(db: Session, user_id: int, start: datetime, end: datetime) -> Expense | None:
    return db.scalar(
        select(Expense).where(*_in_range(user_id, start, end)).order_by(Expense.amount.desc()).limit(1)
    )


def create(
    db: Session, user_id: int, amount: Decimal, category: str, description: str | None, spent_at: datetime
) -> Expense:
    expense = Expense(
        user_id=user_id, amount=amount, category=category, description=description, spent_at=spent_at
    )
    db.add(expense)
    db.flush()
    return expense


def update(
    db: Session,
    expense: Expense,
    amount: Decimal | None = None,
    category: str | None = None,
    description: str | None = None,
    spent_at: datetime | None = None,
) -> None:
    if amount is not None:
        expense.amount = amount
    if category is not None:
        expense.category = category
    if description is not None:
        expense.description = description
    if spent_at is not None:
        expense.spent_at = spent_at
    db.flush()


def delete(db: Session, expense: Expense) -> None:
    db.delete(expense)
    db.flush()
