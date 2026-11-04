from collections.abc import Sequence
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.schemas.pagination import PageParams


def paginate[M](db: Session, query: Select[tuple[M]], params: PageParams) -> tuple[Sequence[M], int]:
    """Run `query` for one page and return (rows, total matching rows)."""
    total_query: Select[Any] = select(func.count()).select_from(query.order_by(None).subquery())
    total = db.scalar(total_query) or 0
    rows = db.scalars(query.limit(params.limit).offset(params.offset)).all()
    return rows, total
