from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import ErrorResponse
from app.schemas.expense import ExpensePage, ExpenseRead
from app.schemas.pagination import PageParams, page_params
from app.services import expense_service

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)


@router.get("", response_model=ExpensePage)
def list_expenses(
    current_user: CurrentUser, db: DbSession, params: Annotated[PageParams, Depends(page_params)]
) -> ExpensePage:
    rows, total = expense_service.list_for_user(db, current_user.id, params)
    return ExpensePage.build(
        [ExpenseRead.model_validate(r) for r in rows],
        total,
        params,
        total_amount=expense_service.total_for_user(db, current_user.id),
    )
