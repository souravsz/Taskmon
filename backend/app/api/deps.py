from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidTokenError, UnauthorizedError
from app.core.security import decode_access_token
from app.database.connection import get_db
from app.models.user import User
from app.services import user_service
from app.services.otp_service import OtpProvider, get_otp_provider

# auto_error=False so a missing header gets our 401 error shape, not FastAPI's default.
_bearer = HTTPBearer(auto_error=False)

DbSession = Annotated[Session, Depends(get_db)]
OtpProviderDep = Annotated[OtpProvider, Depends(get_otp_provider)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    if credentials is None:
        raise UnauthorizedError()
    user = user_service.get_by_id(db, decode_access_token(credentials.credentials))
    if user is None:
        raise InvalidTokenError()
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
