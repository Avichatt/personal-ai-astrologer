"""Main FastAPI application factory and lifespan management."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api import api_router

# Resolve the frontend directory path relative to this file
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
from app.config.logging_config import configure_logging, get_logger
from app.config.settings import get_settings
from app.database.connection import engine
from app.schemas.common import ErrorDetail, ErrorResponse
from app.utils.request_id import RequestIdMiddleware, get_current_request_id

logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan context manager for startup and shutdown hooks."""
    configure_logging()
    logger.info("application_starting", version=app.version)
    yield
    logger.info("application_shutting_down")
    await engine.dispose()
    logger.info("database_engine_disposed")


def create_app() -> FastAPI:
    """FastAPI application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── Middlewares ──────────────────────────────
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else ["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Exception Handlers ───────────────────────
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        req_id = get_current_request_id()
        error_resp = ErrorResponse(
            error=ErrorDetail(
                code=f"HTTP_{exc.status_code}",
                message=str(exc.detail),
                request_id=req_id,
            )
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_resp.model_dump(),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        req_id = get_current_request_id()
        error_resp = ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Invalid request parameters.",
                details={"errors": exc.errors()},
                request_id=req_id,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_resp.model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = get_current_request_id()
        logger.error("unhandled_exception", error=str(exc), request_id=req_id, exc_info=True)
        error_resp = ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected internal error occurred. Please try again later.",
                request_id=req_id,
            )
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_resp.model_dump(),
        )

    # ── Health Endpoints ─────────────────────────
    @app.get("/health", tags=["Health"])
    @app.get("/health/live", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "ok", "version": settings.app_version}

    @app.get("/health/ready", tags=["Health"])
    async def readiness_check() -> dict[str, str]:
        """Readiness probe."""
        return {"status": "ready", "version": settings.app_version}

    # ── Routers ──────────────────────────────────
    app.include_router(api_router)

    # ── Frontend (Static Files + SPA Root) ──────
    if FRONTEND_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

        @app.get("/", include_in_schema=False)
        async def serve_frontend() -> FileResponse:
            """Serve the frontend SPA."""
            return FileResponse(str(FRONTEND_DIR / "index.html"))

    return app


app = create_app()
