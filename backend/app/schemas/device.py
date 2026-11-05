from typing import Literal

from pydantic import BaseModel, Field


class DeviceRegister(BaseModel):
    """The phone's FCM token, sent after login and whenever Firebase gives the app a new one."""

    token: str = Field(min_length=1, max_length=512)
    platform: Literal["android", "ios"] = "android"


class DeviceUnregister(BaseModel):
    """Sent on logout so the phone stops getting this user's reminders."""

    token: str = Field(min_length=1, max_length=512)
