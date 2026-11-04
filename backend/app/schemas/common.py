import re
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field

from app.core.config import settings

_SEPARATORS = re.compile(r"[\s\-().]")
_E164 = re.compile(r"^\+[1-9]\d{9,14}$")


def normalize_mobile(value: str) -> str:
    """Normalise to E.164. Bare 10-digit numbers get DEFAULT_COUNTRY_CODE."""
    digits = _SEPARATORS.sub("", value)
    if not digits.startswith("+"):
        digits = f"+{settings.DEFAULT_COUNTRY_CODE}{digits}" if len(digits) == 10 else f"+{digits}"
    if not _E164.match(digits):
        raise ValueError("Enter a valid mobile number")
    return digits


MobileNumber = Annotated[
    str,
    Field(max_length=20, examples=["+919876543210"]),
    AfterValidator(normalize_mobile),
]


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
    code: str
