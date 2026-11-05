from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base
from app.models.mixins import TimestampMixin, UserOwnedMixin


class DeviceToken(UserOwnedMixin, TimestampMixin, Base):
    """A phone's FCM token: where the reminder worker sends this user's push notifications.

    One row per phone. A token is unique: logging in as someone else on the same phone moves it.
    """

    __tablename__ = "device_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    platform: Mapped[str] = mapped_column(String(16), nullable=False)  # android | ios
