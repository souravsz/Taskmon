from collections.abc import Sequence

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.models.note import Note
from app.schemas.pagination import PageParams
from app.services.pagination import paginate


def list_for_user(db: Session, user_id: int, params: PageParams) -> tuple[Sequence[Note], int]:
    """Most recently edited first."""
    query = select(Note).where(Note.user_id == user_id).order_by(Note.updated_at.desc(), Note.id.desc())
    return paginate(db, query, params)


def _with_words(query: Select[tuple[Note]], text: str | None) -> Select[tuple[Note]]:
    for word in (text or "").split():
        query = query.where(or_(Note.title.ilike(f"%{word}%"), Note.content.ilike(f"%{word}%")))
    return query


def list_recent(db: Session, user_id: int, limit: int = 10) -> tuple[list[Note], int]:
    rows, total = list_for_user(db, user_id, PageParams(limit=limit, offset=0))
    return list(rows), total


def search(db: Session, user_id: int, text: str, limit: int = 20) -> list[Note]:
    """Notes containing every word, in the title or the content. Title matches first."""
    query = _with_words(select(Note).where(Note.user_id == user_id), text)
    rows = list(db.scalars(query.order_by(Note.updated_at.desc(), Note.id.desc()).limit(limit)))
    words = [w.lower() for w in text.split()]
    return sorted(rows, key=lambda n: not all(w in n.title.lower() for w in words))


def latest(db: Session, user_id: int) -> Note | None:
    return db.scalar(select(Note).where(Note.user_id == user_id).order_by(Note.id.desc()).limit(1))


def create(db: Session, user_id: int, title: str, content: str | None) -> Note:
    note = Note(user_id=user_id, title=title, content=content)
    db.add(note)
    db.flush()
    return note


def update(
    db: Session, note: Note, title: str | None = None, content: str | None = None, append: str | None = None
) -> None:
    if title is not None:
        note.title = title
    if content is not None:
        note.content = content
    if append:
        note.content = f"{note.content}\n{append}" if note.content else append
    db.flush()


def delete(db: Session, note: Note) -> None:
    db.delete(note)
    db.flush()
