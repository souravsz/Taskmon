from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import MobileNumber
from app.schemas.user import UserRead


class SendOtpRequest(BaseModel):
    mobile_number: MobileNumber


class VerifyOtpRequest(BaseModel):
    mobile_number: MobileNumber
    otp: str = Field(pattern=r"^\d{4,8}$", examples=["1234"])


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105
    expires_in: int = Field(description="Token lifetime in seconds")
    has_username: bool
    user: UserRead
