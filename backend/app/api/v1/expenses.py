import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import CurrentUser, DbSession
from app.core.exceptions import NotFoundError
from app.schemas.common import ErrorResponse
from app.schemas.expense import ExpenseCountedUpdate, ExpensePage, ExpenseRead
from app.schemas.pagination import PageParams, page_params
from app.services import expense_service

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/expenses",
    tags=["expenses"],
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)


@router.get("", response_model=ExpensePage)
def list_expenses(
    current_user: CurrentUser,
    db: DbSession,
    params: Annotated[PageParams, Depends(page_params)],
    include_uncounted: Annotated[bool, Query(description="Also list expenses marked don't count")] = False,
) -> ExpensePage:
    rows, total = expense_service.list_for_user(db, current_user.id, params, include_uncounted)
    return ExpensePage.build(
        [ExpenseRead.model_validate(r) for r in rows],
        total,
        params,
        total_amount=expense_service.total_for_user(db, current_user.id),
    )


@router.put(
    "/{expense_id}/counted",
    response_model=ExpenseRead,
    summary="Count or don't count an expense (the payment notification's Don't count button)",
    responses={404: {"model": ErrorResponse, "description": "No such expense for this user"}},
)
def set_expense_counted(
    expense_id: int, body: ExpenseCountedUpdate, current_user: CurrentUser, db: DbSession
) -> ExpenseRead:
    expense = expense_service.get_for_user(db, current_user.id, expense_id)
    if expense is None:
        raise NotFoundError("Expense not found")
    expense_service.set_counted(db, expense, body.counted)
    db.commit()
    db.refresh(expense)
    logger.info("Expense counted=%s: expense=%s user=%s", body.counted, expense_id, current_user.id)
    return ExpenseRead.model_validate(expense)
