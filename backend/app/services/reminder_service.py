from collections.abc import Sequence
from datetime import date, datetime, time, timedelta

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.notification_task import NotificationTask
from app.schemas.pagination import PageParams
from app.services.pagination import paginate


def list_for_user(db: Session, user_id: int, params: PageParams) -> tuple[Sequence[NotificationTask], int]:
    """Open reminders first, soonest first; completed ones after."""
    query = (
        select(NotificationTask)
        .where(NotificationTask.user_id == user_id)
        .order_by(NotificationTask.is_completed, NotificationTask.notify_at, NotificationTask.id)
    )
    return paginate(db, query, params)


def _open(user_id: int) -> Select[tuple[NotificationTask]]:
    return select(NotificationTask).where(
        NotificationTask.user_id == user_id,
        NotificationTask.is_completed.is_(False),
        NotificationTask.is_cancelled.is_(False),
    )


def _with_words(query: Select[tuple[NotificationTask]], text: str | None) -> Select[tuple[NotificationTask]]:
    for word in (text or "").split():
        query = query.where(NotificationTask.title.ilike(f"%{word}%"))
    return query


def list_open(
    db: Session, user_id: int, start: datetime | None = None, end: datetime | None = None, limit: int = 10
) -> tuple[list[NotificationTask], int]:
    """Open (not completed, not cancelled) reminders, soonest first, and how many there are in total."""
    query = _open(user_id)
    if start:
        query = query.where(NotificationTask.notify_at >= start)
    if end:
        query = query.where(NotificationTask.notify_at < end)
    rows, total = paginate(
        db, query.order_by(NotificationTask.notify_at, NotificationTask.id), PageParams(limit=limit, offset=0)
    )
    return list(rows), total


def search(db: Session, user_id: int, text: str, limit: int = 10) -> list[NotificationTask]:
    query = _with_words(select(NotificationTask).where(NotificationTask.user_id == user_id), text)
    return list(db.scalars(query.order_by(NotificationTask.notify_at.desc()).limit(limit)))


def find(
    db: Session,
    user_id: int,
    text: str | None = None,
    day: date | None = None,
    at: time | None = None,
    include_closed: bool = False,
    limit: int = 20,
) -> list[NotificationTask]:
    """Reminders matching every given criterion (used to find the target of update / cancel / delete)."""
    query = (
        select(NotificationTask).where(NotificationTask.user_id == user_id)
        if include_closed
        else _open(user_id)
    )
    query = _with_words(query, text)
    if day:
        start = datetime.combine(day, time())
        query = query.where(
            NotificationTask.notify_at >= start, NotificationTask.notify_at < start + timedelta(days=1)
        )
    rows = list(db.scalars(query.order_by(NotificationTask.notify_at, NotificationTask.id).limit(limit * 5)))
    if at:  # hour:minute compared in Python so it works the same on MySQL and SQLite
        rows = [r for r in rows if r.notify_at.time().replace(second=0, microsecond=0) == at]
    return rows[:limit]


def get_for_user(db: Session, user_id: int, reminder_id: int) -> NotificationTask | None:
    """The reminder, only if it belongs to this user."""
    return db.scalar(
        select(NotificationTask).where(
            NotificationTask.id == reminder_id, NotificationTask.user_id == user_id
        )
    )


def latest(db: Session, user_id: int) -> NotificationTask | None:
    return db.scalar(
        select(NotificationTask)
        .where(NotificationTask.user_id == user_id)
        .order_by(NotificationTask.id.desc())
        .limit(1)
    )


def create(
    db: Session, user_id: int, title: str, notify_at: datetime, recurrence: str | None = None
) -> NotificationTask:
    reminder = NotificationTask(user_id=user_id, title=title, notify_at=notify_at, recurrence=recurrence)
    db.add(reminder)
    db.flush()
    return reminder


def update(
    db: Session, reminder: NotificationTask, title: str | None = None, notify_at: datetime | None = None
) -> None:
    if title is not None:
        reminder.title = title
    if notify_at is not None:
        reminder.notify_at = notify_at
        reminder.is_notified = False  # a moved reminder fires again
        reminder.notified_at = None
    db.flush()


def complete(db: Session, reminder: NotificationTask) -> None:
    reminder.is_completed = True
    db.flush()


def cancel(db: Session, reminder: NotificationTask) -> None:
    """Stops it firing; the record is kept (unlike delete)."""
    reminder.is_cancelled = True
    db.flush()


def delete(db: Session, reminder: NotificationTask) -> None:
    db.delete(reminder)
    db.flush()
