from collections.abc import Sequence

from sqlalchemy import select
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
