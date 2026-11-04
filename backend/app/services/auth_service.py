import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import InvalidOtpError
from app.core.security import create_access_token, mask_mobile
from app.models.user import User
from app.services import user_service
from app.services.otp_service import OtpProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LoginResult:
    user: User
    access_token: str
    expires_in: int


def request_otp(otp_provider: OtpProvider, mobile_number: str) -> None:
    otp_provider.send(mobile_number)


def login_with_otp(db: Session, otp_provider: OtpProvider, mobile_number: str, otp: str) -> LoginResult:
    if not otp_provider.verify(mobile_number, otp):
        logger.info("Failed OTP attempt for %s", mask_mobile(mobile_number))
        raise InvalidOtpError()

    user = user_service.get_or_create_by_mobile(db, mobile_number)
    logger.info("User %s logged in", user.id)
    return LoginResult(
        user=user,
        access_token=create_access_token(user.id),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
