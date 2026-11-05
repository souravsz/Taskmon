"""Reminder worker: every WORKER_INTERVAL_SECONDS, sends a push for each reminder that is due.

The database is the schedule. Creating, moving, cancelling or deleting a reminder only changes its row
in notification_tasks; this loop sends whatever is due. Nothing is lost on a restart: a reminder that
came due while the worker was down is sent on the next run (or skipped if it's over an hour late).

Run: python -m app.worker  (same Docker image as the API, separate container)
"""

import logging
import signal
import threading
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.response_generator import clock
from app.conversation.action_handler import add_period
from app.core.config import settings
from app.core.logging import configure_logging
from app.database.connection import SessionLocal
from app.models.notification_task import NotificationTask
from app.models.user import User
from app.services import device_service, push_service

logger = logging.getLogger("app.worker")

MISSED_AFTER = timedelta(hours=1)  # found later than this (worker was down): marked done, no push
BATCH = 100  # reminders per timezone per run


def due_reminders(db: Session, now_utc: datetime) -> list[tuple[NotificationTask, datetime]]:
    """(reminder, the user's local now) for every open reminder whose time has come.

    notify_at is stored in the user's local time, so "due" is checked per timezone. Rows are locked
    (SKIP LOCKED) until commit, so two workers never send the same reminder."""
    due: list[tuple[NotificationTask, datetime]] = []
    for tz in db.scalars(select(User.timezone).distinct()).all():
        try:
            local_now = now_utc.astimezone(ZoneInfo(tz)).replace(tzinfo=None)
        except (ZoneInfoNotFoundError, ValueError):
            logger.error("Unknown timezone %r: its users' reminders are skipped", tz)
            continue
        query = (
            select(NotificationTask)
            .join(User, User.id == NotificationTask.user_id)
            .where(
                User.timezone == tz,
                NotificationTask.is_notified.is_(False),
                NotificationTask.is_cancelled.is_(False),
                NotificationTask.is_completed.is_(False),
                NotificationTask.notify_at <= local_now,
            )
            .order_by(NotificationTask.notify_at, NotificationTask.id)
            .limit(BATCH)
            .with_for_update(skip_locked=True, of=NotificationTask)
        )
        due += [(reminder, local_now) for reminder in db.scalars(query)]
    return due


def next_occurrence(at: datetime, recurrence: str, now: datetime) -> datetime:
    """The first repeat after `now` (missed repeats are skipped); weekdays skip Saturday and Sunday."""
    at = add_period(at, recurrence)
    while at <= now or (recurrence == "weekdays" and at.weekday() >= 5):
        at = add_period(at, recurrence)
    return at


def notify(db: Session, reminder: NotificationTask, now: datetime) -> None:
    """Sends the push for one due reminder, then marks it done (or moves a repeating one forward)."""
    late = now - reminder.notify_at
    if late > MISSED_AFTER:
        logger.info("reminder=%s user=%s skipped: %s late", reminder.id, reminder.user_id, late)
    else:
        tokens = device_service.tokens_for_user(db, reminder.user_id)
        data = {"type": "reminder", "reminder_id": str(reminder.id)}
        results = {
            token: push_service.send(token, reminder.title, f"Reminder · {clock(reminder.notify_at)}", data)
            for token in tokens
        }
        dead = [token for token, result in results.items() if result == "dead"]
        device_service.delete_tokens(db, dead)
        logger.info(
            "reminder=%s user=%s %r: phones=%d sent=%d dead=%d failed=%d",
            reminder.id,
            reminder.user_id,
            reminder.title,
            len(tokens),
            list(results.values()).count("sent"),
            len(dead),
            list(results.values()).count("failed"),
        )
        if "failed" in results.values() and "sent" not in results.values():
            return  # nothing delivered because of FCM trouble: left due, so the next run tries again

    reminder.notified_at = now
    if reminder.recurrence:
        reminder.notify_at = next_occurrence(reminder.notify_at, reminder.recurrence, now)
        logger.info(
            "reminder=%s repeats %s: next at %s", reminder.id, reminder.recurrence, reminder.notify_at
        )
    else:
        reminder.is_notified = True


def run_once(db: Session, now_utc: datetime | None = None) -> int:
    """One pass: every due reminder is handled and committed. Returns how many were due."""
    due = due_reminders(db, now_utc or datetime.now(UTC))
    for reminder, local_now in due:
        notify(db, reminder, local_now)
    db.commit()
    if due:
        logger.info("Run finished: %d due", len(due))
    return len(due)


def main() -> None:
    configure_logging()
    push_service.check_credentials()  # a missing or broken key stops the worker here, with the reason
    stop = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop.set())  # docker stop
    signal.signal(signal.SIGINT, lambda *_: stop.set())  # Ctrl+C
    logger.info("Reminder worker started: checking every %ss", settings.WORKER_INTERVAL_SECONDS)

    while not stop.is_set():
        with SessionLocal() as db:
            try:
                run_once(db)
            except Exception:
                db.rollback()
                logger.exception("Reminder run failed; trying again next interval")
        stop.wait(settings.WORKER_INTERVAL_SECONDS)
    logger.info("Reminder worker stopped")


if __name__ == "__main__":
    main()
