import logging

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.device_token import DeviceToken

logger = logging.getLogger(__name__)


def register(db: Session, user_id: int, token: str, platform: str) -> None:
    """Saves the phone's token for this user. A token already saved for another user moves to this one
    (someone logged in with a different account on the same phone)."""
    device = db.scalar(select(DeviceToken).where(DeviceToken.token == token))
    if device is None:
        db.add(DeviceToken(user_id=user_id, token=token, platform=platform))
        logger.info("Device registered: user=%s platform=%s", user_id, platform)
    elif device.user_id != user_id or device.platform != platform:
        logger.info("Device moved: user=%s → user=%s", device.user_id, user_id)
        device.user_id, device.platform = user_id, platform
    db.commit()


def unregister(db: Session, user_id: int, token: str) -> None:
    db.execute(delete(DeviceToken).where(DeviceToken.user_id == user_id, DeviceToken.token == token))
    db.commit()
    logger.info("Device unregistered: user=%s", user_id)


def tokens_for_user(db: Session, user_id: int) -> list[str]:
    return list(db.scalars(select(DeviceToken.token).where(DeviceToken.user_id == user_id)))


def delete_tokens(db: Session, tokens: list[str]) -> None:
    """Removes tokens Firebase says are no longer valid (app uninstalled, data cleared)."""
    if tokens:
        db.execute(delete(DeviceToken).where(DeviceToken.token.in_(tokens)))
        db.flush()
