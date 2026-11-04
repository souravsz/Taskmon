from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import ErrorResponse
from app.schemas.note import NoteRead
from app.schemas.pagination import Page, PageParams, page_params
from app.services import note_service

router = APIRouter(
    prefix="/notes",
    tags=["notes"],
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)


@router.get("", response_model=Page[NoteRead])
def list_notes(
    current_user: CurrentUser, db: DbSession, params: Annotated[PageParams, Depends(page_params)]
) -> Page[NoteRead]:
    rows, total = note_service.list_for_user(db, current_user.id, params)
    return Page[NoteRead].build([NoteRead.model_validate(r) for r in rows], total, params)
