import logging
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.schemas.common import ErrorResponse
from app.schemas.pagination import Page, PageParams, page_params
from app.schemas.reminder import ReminderRead
from app.services import reminder_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/reminders",
    tags=["reminders"],
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)


@router.get("", response_model=Page[ReminderRead])
def list_reminders(
    current_user: CurrentUser, db: DbSession, params: Annotated[PageParams, Depends(page_params)]
) -> Page[ReminderRead]:
    rows, total = reminder_service.list_for_user(db, current_user.id, params)
    return Page[ReminderRead].build([ReminderRead.model_validate(r) for r in rows], total, params)


@router.post(
    "/{reminder_id}/complete",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Mark a reminder done (the push notification's Done button)",
    responses={404: {"model": ErrorResponse, "description": "No such reminder for this user"}},
)
def complete_reminder(reminder_id: int, current_user: CurrentUser, db: DbSession) -> None:
    reminder = reminder_service.get_for_user(db, current_user.id, reminder_id)
    if reminder is None:
        raise NotFoundError("Reminder not found")
    reminder_service.complete(db, reminder)
    db.commit()
    logger.info("Reminder completed from notification: reminder=%s user=%s", reminder_id, current_user.id)
