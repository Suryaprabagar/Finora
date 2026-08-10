"""Finora FastAPI application factory."""
import logging
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from app.core.config import settings
from app.core.database import engine
from app.api.v1.router import api_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Finora - Personal Financial Management API. Where your financial future begins.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
async def health_check():
    """Application liveness check — does NOT probe the database."""
    return {"status": "healthy", "app": settings.PROJECT_NAME, "version": "1.0.0"}


@app.get("/health/db")
async def health_db():
    """
    Deep health check — probes the PostgreSQL connection.

    Returns:
        200  {"status": "healthy", "db": "ok",       "latency_ms": <n>}
        503  {"status": "unhealthy", "db": "error",  "detail": "<reason>"}

    CI uses this to distinguish "app alive" from "app + DB alive".
    Railway can wire this up as the service health-check URL.
    """
    t0 = time.monotonic()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency_ms = round((time.monotonic() - t0) * 1000, 2)
        return {"status": "healthy", "db": "ok", "latency_ms": latency_ms}
    except Exception as exc:
        logger.error(f"DB health check failed: {exc}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "db": "error", "detail": str(exc)},
        )


@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API", "docs": "/api/docs"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    # BUG-004 fix: log full traceback internally, never expose it to the client
    logger.error(f"Unhandled exception on {request.url}: {traceback.format_exc()}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

