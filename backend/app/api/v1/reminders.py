from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import ErrorResponse
from app.schemas.pagination import Page, PageParams, page_params
from app.schemas.reminder import ReminderRead
from app.services import reminder_service

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
