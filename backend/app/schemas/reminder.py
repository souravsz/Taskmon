from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ReminderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str | None
    notify_at: datetime
    is_notified: bool
    is_completed: bool
    task_id: int | None
