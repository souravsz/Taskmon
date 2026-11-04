from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import settings
from app.core.exceptions import InvalidTokenError

ACCESS_TOKEN_TYPE = "access"  # noqa: S105  (JWT claim value, not a secret)


def create_access_token(user_id: int, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": str(user_id), "type": ACCESS_TOKEN_TYPE, "iat": now, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET_KEY.get_secret_value(), algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> int:
    """Validate an access token and return the user id it was issued for."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY.get_secret_value(),
            algorithms=[settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "type"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise InvalidTokenError("Token has expired") from exc
    except jwt.PyJWTError as exc:
        raise InvalidTokenError() from exc

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise InvalidTokenError()
    try:
        return int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise InvalidTokenError() from exc


def mask_mobile(mobile_number: str) -> str:
    """'+919876543210' → '+91******3210', safe for logs."""
    if len(mobile_number) <= 7:
        return "*" * len(mobile_number)
    return f"{mobile_number[:3]}{'*' * (len(mobile_number) - 7)}{mobile_number[-4:]}"
