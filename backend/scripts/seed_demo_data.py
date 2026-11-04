"""Insert sample reminders, expenses and notes for one user (local development only).

Usage (from backend/):
    .venv\\Scripts\\python -m scripts.seed_demo_data 9876543210
    .venv\\Scripts\\python -m scripts.seed_demo_data 9876543210 --clear   # remove all three first
"""

import argparse
import sys
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete

from app.core.config import settings
from app.database.connection import SessionLocal
from app.models import Expense, Note, NotificationTask
from app.schemas.common import normalize_mobile
from app.services import user_service

REMINDERS = [
    ("Call Mom", 0, 19),
    ("Renew car insurance", 1, 10),
    ("Dentist appointment", 2, 16),
    ("Pay electricity bill", 3, 9),
    ("Book train tickets", 5, 11),
]
EXPENSES = [
    ("450.00", "Food", "Lunch"),
    ("1220.00", "Groceries", "Weekly groceries"),
    ("640.00", "Transport", "Metro card"),
    ("180.00", "Food", "Coffee"),
    ("299.00", "Misc", "Phone recharge"),
]
NOTES = [
    ("Gift ideas for Riya's birthday", "Books, a plant, concert tickets"),
    ("Books to read", "Atomic Habits, Deep Work"),
    ("Wi-Fi password", "Ask the landlord"),
    ("Trip packing list", "Charger, passport, sunscreen"),
]


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("mobile", help="The user's mobile number, e.g. 9876543210")
    parser.add_argument("--clear", action="store_true", help="Delete the user's existing rows first")
    args = parser.parse_args()

    if settings.is_production:
        print("Refusing to seed demo data in production.")
        return 1

    with SessionLocal() as db:
        user = user_service.get_by_mobile(db, normalize_mobile(args.mobile))
        if user is None:
            print("No user with that number. Log in once from the app first.")
            return 1

        if args.clear:
            for model in (NotificationTask, Expense, Note):
                db.execute(delete(model).where(model.user_id == user.id))

        today = datetime.now().replace(minute=0, second=0, microsecond=0)
        db.add_all(
            NotificationTask(user_id=user.id, title=t, notify_at=(today + timedelta(days=d)).replace(hour=h))
            for t, d, h in REMINDERS
        )
        db.add_all(
            Expense(
                user_id=user.id,
                amount=Decimal(a),
                category=c,
                description=desc,
                spent_at=today - timedelta(days=i),
            )
            for i, (a, c, desc) in enumerate(EXPENSES)
        )
        db.add_all(Note(user_id=user.id, title=t, content=body) for t, body in NOTES)
        db.commit()
        print(
            f"Seeded {len(REMINDERS)} reminders, {len(EXPENSES)} expenses, {len(NOTES)} notes "
            f"for user {user.id} ({user.username or 'no username'})."
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
