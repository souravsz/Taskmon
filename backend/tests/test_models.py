from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import (
    Conversation,
    Expense,
    Message,
    MessageRole,
    Note,
    NotificationTask,
    Task,
    User,
    UserDetail,
)


def _user(db: Session) -> User:
    user = User(mobile_number="+919876543210", expense_limit=Decimal("5000.00"))
    db.add(user)
    db.commit()
    return user


def test_conversation_keeps_messages_in_order(db_session: Session) -> None:
    user = _user(db_session)
    convo = Conversation(user_id=user.id, title="Planning")
    convo.messages = [
        Message(role=MessageRole.USER, content="Remind me to call Mom at 7 pm"),
        Message(role=MessageRole.ASSISTANT, content="Done. I'll nudge you today at 7:00 PM."),
    ]
    db_session.add(convo)
    db_session.commit()
    db_session.expire_all()

    loaded = db_session.get(Conversation, convo.id)
    assert loaded is not None
    assert [m.role for m in loaded.messages] == [MessageRole.USER, MessageRole.ASSISTANT]
    assert loaded.messages[0].created_at is not None


def test_user_owned_rows_get_server_defaults(db_session: Session) -> None:
    user = _user(db_session)
    task = Task(user_id=user.id, title="Pay electricity bill")
    reminder = NotificationTask(
        user_id=user.id, title="Call Mom", notify_at=datetime.now() + timedelta(hours=2)
    )
    db_session.add_all(
        [
            task,
            reminder,
            Note(user_id=user.id, title="Books to read"),
            Expense(user_id=user.id, amount=Decimal("450.00"), category="Food"),
            UserDetail(user_id=user.id, content="Prefers reminders in the evening."),
        ]
    )
    db_session.commit()
    db_session.refresh(task)
    db_session.refresh(reminder)

    assert task.is_completed is False
    assert reminder.is_notified is False
    assert reminder.is_completed is False
    assert user.expense_limit == Decimal("5000.00")
