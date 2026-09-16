"""Sync API — Google Drive synchronization status and control endpoints.

Endpoints:
    GET  /api/v1/sync/status   — current sync status
    POST /api/v1/sync/trigger  — manual sync (uploads current state to Drive)
    GET  /api/v1/sync/versions — list all stored Drive versions

These endpoints are deliberately READ-ONLY for status and single-trigger for
manual saves. They do NOT expose raw Drive API operations to the client.

IMPORTANT: Drive calls here go through StorageManager only. Never call
google_drive.py directly from this file.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Depends

from app.core.config import settings
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.common import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def _get_manager():
    """Return the running StorageManager (imported lazily to avoid circular imports)."""
    from app.main import get_storage_manager
    return get_storage_manager()


@router.get("/status")
async def sync_status(current_user: User = Depends(get_current_user)):
    """Return the current Google Drive synchronization status.

    Returns a dict with fields:
        - google_drive:   connected | syncing | current | offline | error | disabled
        - last_sync:      ISO-8601 timestamp or null
        - local_state:    current (SQLite is always the live runtime)
        - cloud_state:    mirrors google_drive status
        - versions:       number of permanent versions on Drive
        - max_versions:   configured maximum
        - drive_enabled:  bool
    """
    sm = _get_manager()
    if sm is None:
        return APIResponse(data={
            "google_drive": "disabled",
            "last_sync": None,
            "local_state": "current",
            "cloud_state": "disabled",
            "versions": 0,
            "max_versions": settings.MAX_VERSIONS,
            "drive_enabled": False,
        })
    return APIResponse(data=sm.get_status())


@router.post("/trigger")
async def trigger_sync(current_user: User = Depends(get_current_user)):
    """Trigger a manual synchronization — exports SQLite and uploads to Drive.

    This creates a permanent new version only if Drive is enabled.
    If Drive is disabled, returns a clear message rather than an error.

    Note: This does NOT affect the rolling version count immediately;
    cleanup runs as part of the save operation.
    """
    sm = _get_manager()
    if sm is None or not settings.GOOGLE_DRIVE_ENABLED:
        return APIResponse(
            data={"synced": False},
            message="Google Drive sync is disabled. Set GOOGLE_DRIVE_ENABLED=true to enable.",
        )

    try:
        success = await sm.save_state(reason="manual")
        if success:
            return APIResponse(
                data={"synced": True, **sm.get_status()},
                message="State saved to Google Drive successfully.",
            )
        else:
            raise HTTPException(
                status_code=503,
                detail="Sync failed — check server logs for details. Local data is intact.",
            )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Manual sync error: {exc}", exc_info=True)
        raise HTTPException(
            status_code=503,
            detail=f"Sync error: {exc}. Local data is intact.",
        )


@router.get("/versions")
async def list_versions(current_user: User = Depends(get_current_user)):
    """List all permanent Drive versions available for restore.

    Returns a list of version labels such as ['v001', 'v002', 'v003'].
    Returns an empty list when Drive is disabled.
    """
    sm = _get_manager()
    if sm is None or not settings.GOOGLE_DRIVE_ENABLED:
        return APIResponse(data={"versions": []})
    try:
        versions = await sm.list_versions()
        return APIResponse(data={"versions": versions})
    except Exception as exc:
        logger.error(f"Failed to list versions: {exc}", exc_info=True)
        raise HTTPException(status_code=503, detail=f"Could not list Drive versions: {exc}")
