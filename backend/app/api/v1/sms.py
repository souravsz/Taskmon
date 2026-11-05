from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.schemas.common import ErrorResponse
from app.schemas.sms import BankSmsIn, BankSmsResult
from app.services import sms_service

router = APIRouter(
    prefix="/sms",
    tags=["sms"],
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)


@router.post("/bank", response_model=BankSmsResult, summary="Record the debit in a bank SMS as an expense")
def record_bank_sms(body: BankSmsIn, current_user: CurrentUser, db: DbSession) -> BankSmsResult:
    """Federal Bank debit alerts become expenses (once per bank reference). If the day's spending passes
    the user's daily budget, a warning push goes to their phones. Any other text is ignored."""
    result = sms_service.record(db, current_user, body.text)
    expense = result.expense
    return BankSmsResult(
        recorded=result.recorded,
        reason=result.reason,
        expense_id=expense.id if expense else None,
        amount=expense.amount if expense else None,
        spent_at=expense.spent_at if expense else None,
        description=expense.description if expense else None,
        spent_today=result.spent_today,
        daily_budget=result.daily_budget,
        over_budget=result.over_budget,
    )
