"""Finora storage package — Google Drive persistence layer.

This package handles all cloud persistence concerns and is the only
place in Finora that contains Google Drive API calls.

Modules:
    google_drive     — low-level Drive API operations
    state_serializer — state export/import wrapping backup_service
    lock_manager     — single-instance lock to prevent concurrent writes
    storage_manager  — high-level orchestration (load/save/version/cleanup)
    autosave         — background autosave asyncio task
"""
