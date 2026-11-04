from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

Username = Annotated[
    str,
    StringConstraints(strip_whitespace=True, pattern=r"^[A-Za-z0-9_]{3,30}$"),
    Field(description="3-30 characters: letters, numbers and underscore", examples=["john_doe"]),
]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mobile_number: str
    username: str | None
    created_at: datetime


class UsernameUpdate(BaseModel):
    username: Username
