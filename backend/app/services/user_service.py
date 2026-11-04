from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import UsernameTakenError
from app.models.user import User


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def get_by_mobile(db: Session, mobile_number: str) -> User | None:
    return db.scalar(select(User).where(User.mobile_number == mobile_number))


def get_or_create_by_mobile(db: Session, mobile_number: str) -> User:
    user = get_by_mobile(db, mobile_number)
    if user is not None:
        return user

    user = User(mobile_number=mobile_number)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        # A concurrent request created the same user first: use that row.
        db.rollback()
        existing = get_by_mobile(db, mobile_number)
        if existing is None:
            raise
        return existing
    db.refresh(user)
    return user


def set_username(db: Session, user: User, username: str) -> User:
    if user.username == username:
        return user

    taken = db.scalar(select(User.id).where(User.username == username, User.id != user.id))
    if taken is not None:
        raise UsernameTakenError()

    user.username = username
    try:
        db.commit()
    except IntegrityError as exc:
        # Lost a race on the unique constraint (or a case-insensitive collation match).
        db.rollback()
        raise UsernameTakenError() from exc
    db.refresh(user)
    return user
