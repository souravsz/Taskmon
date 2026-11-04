from typing import Annotated, Any, Self

from fastapi import Query
from pydantic import BaseModel

MAX_PAGE_SIZE = 100


class PageParams(BaseModel):
    limit: int
    offset: int


def page_params(
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE, description="Items per page")] = 20,
    offset: Annotated[int, Query(ge=0, description="Items to skip")] = 0,
) -> PageParams:
    return PageParams(limit=limit, offset=offset)


class Page[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
    has_more: bool

    @classmethod
    def build(cls, items: list[T], total: int, params: PageParams, **extra: Any) -> Self:
        """`extra` fills fields added by subclasses (e.g. ExpensePage.total_amount)."""
        return cls(
            items=items,
            total=total,
            limit=params.limit,
            offset=params.offset,
            has_more=params.offset + len(items) < total,
            **extra,
        )
