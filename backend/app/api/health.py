import logging

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.api.deps import DbSession
from app.database.connection import ping_database

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", summary="Liveness: the process is up")
def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", summary="Readiness: dependencies (database) are reachable")
def readiness(db: DbSession) -> JSONResponse:
    try:
        ping_database(db)
    except Exception:
        logger.exception("Readiness check failed: database unreachable")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unavailable", "database": "down"},
        )
    return JSONResponse(content={"status": "ok", "database": "up"})
