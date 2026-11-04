import hmac
import logging
from typing import Protocol

from app.core.config import settings
from app.core.security import mask_mobile

logger = logging.getLogger(__name__)


class OtpProvider(Protocol):
    """Sends and checks one-time codes. Swap in an SMS-backed implementation later."""

    def send(self, mobile_number: str) -> None: ...

    def verify(self, mobile_number: str, code: str) -> bool: ...


class StaticOtpProvider:
    """Accepts one fixed code for every number. Development only; no SMS is sent."""

    def __init__(self, code: str) -> None:
        self._code = code

    def send(self, mobile_number: str) -> None:
        logger.info("OTP requested for %s (static provider, no SMS sent)", mask_mobile(mobile_number))

    def verify(self, mobile_number: str, code: str) -> bool:
        return hmac.compare_digest(code.encode(), self._code.encode())


def get_otp_provider() -> OtpProvider:
    return StaticOtpProvider(settings.STATIC_OTP)
