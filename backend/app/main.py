"""Finora FastAPI application factory with Google Drive persistence lifespan."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine, AsyncSessionLocal
from app.api.v1.router import api_router
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

logger = logging.getLogger(__name__)

# ── Global StorageManager / AutosaveTask instances ─────────────────────────────
# Stored here so the /sync endpoints can reference the running instance.
_storage_manager = None
_autosave_task = None


def get_storage_manager():
    """Return the active StorageManager instance (may be None if not initialized)."""
    return _storage_manager


# ── Lifespan: startup + shutdown ───────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.

    Startup sequence
    ────────────────
    1. Ensure local .finora/ cache directories exist.
    2. If GOOGLE_DRIVE_ENABLED: authenticate → restore state from Drive.
    3. Start autosave background task.

    Shutdown sequence
    ─────────────────
    1. Stop autosave task.
    2. If GOOGLE_DRIVE_ENABLED: save state to Drive → cleanup old versions.
    3. Release instance lock.
    """
    global _storage_manager, _autosave_task

    print("\n" + "=" * 60)
    print("  Finora Backend Startup")
    print("=" * 60)

    # ── Startup ───────────────────────────────────────────────────────────────
    if settings.GOOGLE_DRIVE_ENABLED:
        print("\n[2/4] Initializing Google Drive sync...")
        try:
            from app.storage.storage_manager import StorageManager
            from app.storage.autosave import AutosaveTask

            _storage_manager = StorageManager(AsyncSessionLocal, settings)
            await _storage_manager.initialize()

            status = _storage_manager.get_status()
            drive_status = status.get("google_drive", "unknown")

            if drive_status in ("connected", "current"):
                restored = await _storage_manager.load_latest_state()
                if restored:
                    print("      State restored successfully.")
                else:
                    print("      No previous Drive state found — starting fresh.")
            elif drive_status == "error":
                print("      [WARNING] Google Drive authentication failed.")
                print("      Continuing with local SQLite data.")
            else:
                print(f"      Drive status: {drive_status}. Continuing with local data.")

            # Start autosave background task
            _autosave_task = AutosaveTask(_storage_manager, settings.AUTOSAVE_INTERVAL)
            _autosave_task.start()
            print(f"      Autosave enabled (every {settings.AUTOSAVE_INTERVAL}s).")

        except Exception as exc:
            logger.error(f"Google Drive initialization failed: {exc}", exc_info=True)
            print(f"      [ERROR] Drive sync init failed: {exc}")
            print("      Continuing with local SQLite data only.")
    else:
        print("\n[2/4] Google Drive sync: DISABLED (set GOOGLE_DRIVE_ENABLED=true to enable).")

    print("\n[3/4] Preparing application...")
    try:
        from app.services.recurring_service import process_due_recurring_expenses
        async with AsyncSessionLocal() as session:
            processed = await process_due_recurring_expenses(session)
            if processed:
                print(f"      Processed {len(processed)} due recurring expense transaction(s).")
    except Exception as exc:
        logger.error(f"Error processing recurring expenses on startup: {exc}", exc_info=True)
        print(f"      [WARNING] Recurring expense processing error: {exc}")

    print("\n[4/4] Starting FastAPI server...")
    print("Finora ready.\n")

    # ── Hand off to the application ───────────────────────────────────────────
    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Finora Backend Shutdown")
    print("=" * 60)

    # Stop autosave first
    if _autosave_task is not None:
        _autosave_task.stop()

    if settings.GOOGLE_DRIVE_ENABLED and _storage_manager is not None:
        print("\nSaving Finora state...")
        try:
            await _storage_manager.shutdown()
            print("Finora closed safely.\n")
        except Exception as exc:
            logger.error(f"Error during Drive shutdown save: {exc}", exc_info=True)
            print(f"[WARNING] Shutdown save failed: {exc}")
            print("Local SQLite data is intact. State was NOT saved to Google Drive.\n")
    else:
        print("Finora closed (Drive sync disabled).\n")


# ── App factory ────────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.APP_VERSION,
    description="Finora - Personal Financial Management API. Where your financial future begins.",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
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


# ── Health endpoints ───────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Application liveness check — does NOT probe the database."""
    return {"status": "healthy", "app": settings.PROJECT_NAME, "version": settings.APP_VERSION}


@app.get("/health/db")
async def health_db():
    """
    Deep health check — probes the SQLite connection.

    Returns:
        200  {"status": "healthy", "db": "ok",      "latency_ms": <n>}
        503  {"status": "unhealthy", "db": "error", "detail": "<reason>"}
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
