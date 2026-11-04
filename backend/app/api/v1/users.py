from fastapi import APIRouter

from app.api.deps import CurrentUser, DbSession
from app.models.user import User
from app.schemas.common import ErrorResponse
from app.schemas.user import UsernameUpdate, UserRead
from app.services import user_service

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={401: {"model": ErrorResponse, "description": "Missing or invalid token"}},
)


@router.get("/me", response_model=UserRead)
def read_me(current_user: CurrentUser) -> User:
    return current_user


@router.put(
    "/me/username",
    response_model=UserRead,
    responses={409: {"model": ErrorResponse, "description": "Username already taken"}},
)
def set_username(body: UsernameUpdate, current_user: CurrentUser, db: DbSession) -> User:
    return user_service.set_username(db, current_user, body.username)
