from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.note import Note
from app.schemas.pagination import PageParams
from app.services.pagination import paginate


def list_for_user(db: Session, user_id: int, params: PageParams) -> tuple[Sequence[Note], int]:
    """Most recently edited first."""
    query = select(Note).where(Note.user_id == user_id).order_by(Note.updated_at.desc(), Note.id.desc())
    return paginate(db, query, params)
