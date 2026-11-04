# Import every model here so Base.metadata is complete for Alembic autogenerate.
from app.models.action_history import ActionHistory
from app.models.conversation import Conversation
from app.models.expense import Expense
from app.models.message import Message, MessageRole
from app.models.note import Note
from app.models.notification_task import NotificationTask
from app.models.pending_action import PendingAction, PendingStatus
from app.models.task import Task
from app.models.user import User
from app.models.user_detail import UserDetail

__all__ = [
    "ActionHistory",
    "Conversation",
    "Expense",
    "Message",
    "MessageRole",
    "Note",
    "NotificationTask",
    "PendingAction",
    "PendingStatus",
    "Task",
    "User",
    "UserDetail",
]
