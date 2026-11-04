from fastapi import APIRouter

from app.api.deps import DbSession, OtpProviderDep
from app.schemas.auth import LoginResponse, SendOtpRequest, VerifyOtpRequest
from app.schemas.common import ErrorResponse, MessageResponse
from app.schemas.user import UserRead
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/send-otp", response_model=MessageResponse)
def send_otp(body: SendOtpRequest, otp_provider: OtpProviderDep) -> MessageResponse:
    auth_service.request_otp(otp_provider, body.mobile_number)
    return MessageResponse(message="OTP sent")


@router.post(
    "/verify-otp",
    response_model=LoginResponse,
    responses={401: {"model": ErrorResponse, "description": "Invalid OTP"}},
)
def verify_otp(body: VerifyOtpRequest, db: DbSession, otp_provider: OtpProviderDep) -> LoginResponse:
    result = auth_service.login_with_otp(db, otp_provider, body.mobile_number, body.otp)
    return LoginResponse(
        access_token=result.access_token,
        expires_in=result.expires_in,
        has_username=result.user.username is not None,
        user=UserRead.model_validate(result.user),
    )
