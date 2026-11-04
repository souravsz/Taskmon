import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.api.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.middleware import REQUEST_ID_HEADER, register_middleware
from app.database.connection import engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting %s v%s (env=%s)", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    if settings.is_production:
        logger.warning("STATIC_OTP is active in production: every number accepts the same code")
    yield
    engine.dispose()
    logger.info("Shutdown complete")


def create_app() -> FastAPI:
    configure_logging()

    docs = settings.DOCS_ENABLED
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        lifespan=lifespan,
        docs_url="/docs" if docs else None,
        redoc_url="/redoc" if docs else None,
        openapi_url="/openapi.json" if docs else None,
    )

    register_middleware(app)
    # Added last so it is outermost: CORS headers are set even on error responses.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", REQUEST_ID_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )
    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
    return app


app = create_app()
