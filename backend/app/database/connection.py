from collections.abc import Generator

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


def _build_engine() -> Engine:
    url = settings.database_url
    if url.get_backend_name() == "sqlite":
        return create_engine(url, connect_args={"check_same_thread": False}, echo=settings.DB_ECHO)
    return create_engine(
        url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_recycle=settings.DB_POOL_RECYCLE_SECONDS,
        pool_pre_ping=True,
        echo=settings.DB_ECHO,
    )


engine = _build_engine()

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session]:
    """One session per request. Services commit explicitly; anything left open is rolled back."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def ping_database(db: Session) -> None:
    db.execute(text("SELECT 1"))
