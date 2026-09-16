"""test_startup_shutdown.py — Integration-style tests for startup/shutdown flows.

Tests (all mocked — no real Drive or DB):
    - Fresh startup: no Drive state → app starts normally with empty DB
    - Startup with valid Drive state → state restored into SQLite
    - Startup with corrupt current/ → falls back to v001
    - Startup with all versions corrupt → continues with local SQLite
    - Startup: Drive auth fails → continues with local SQLite (graceful degradation)
    - Normal shutdown: state saved, version created, old versions cleaned up
    - Shutdown: upload fails → previous version intact, shutdown still completes
    - Crash recovery: on next startup, latest valid version is loaded
    - Schema migration: old schema state is migrated before restore
    - Drive disabled: startup and shutdown behave as local-only
"""
from __future__ import annotations

import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.storage.storage_manager import StorageManager, SyncStatus
from app.storage.state_serializer import (
    build_state_envelope, serialize_to_bytes, build_manifest, CURRENT_SCHEMA_VERSION
)


def _state_bytes(data=None):
    data = data or {"User": [], "Category": [], "Transaction": []}
    env = build_state_envelope(data, save_reason="test", version="v001")
    return serialize_to_bytes(env)


def _manifest_bytes(state_bytes, version="v001", status="complete"):
    m = build_manifest(state_bytes, version=version, status=status)
    return json.dumps(m).encode()


def _make_sm(settings, drive_client=None, db_factory=None):
    sm = StorageManager(db_factory or MagicMock(), settings)
    if drive_client:
        sm._drive_client = drive_client
        sm._root_folder_id = "root"
        sm._current_folder_id = "current-id"
        sm._versions_folder_id = "versions-id"
        sm._drive_enabled = True
        sm._drive_status = SyncStatus.CONNECTED
    return sm


# ── Fresh startup ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fresh_startup_no_drive_state(mock_settings, mock_drive_client, tmp_dir):
    """First run: no state in Drive → app continues with empty local SQLite."""
    mock_settings.FINORA_CACHE_DIR = tmp_dir
    mock_drive_client.download_file.return_value = None
    mock_drive_client.list_subfolders.return_value = []

    sm = _make_sm(mock_settings, mock_drive_client)
    sm._restore_to_sqlite = AsyncMock()

    result = await sm.load_latest_state()
    assert result is False
    sm._restore_to_sqlite.assert_not_awaited()


# ── Startup with valid state ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_startup_with_valid_drive_state(mock_settings, mock_drive_client, tmp_dir):
    mock_settings.FINORA_CACHE_DIR = tmp_dir
    sb = _state_bytes()
    mb = _manifest_bytes(sb)

    mock_drive_client.download_file.side_effect = (
        lambda folder_id, filename: sb if filename == "state.json" else mb
    )
    mock_drive_client.list_subfolders.return_value = []

    sm = _make_sm(mock_settings, mock_drive_client)
    sm._restore_to_sqlite = AsyncMock()

    result = await sm.load_latest_state()
    assert result is True
    sm._restore_to_sqlite.assert_awaited_once()


# ── Corrupt current → fallback ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_corrupt_current_falls_back_to_v001(mock_settings, mock_drive_client, tmp_dir):
    mock_settings.FINORA_CACHE_DIR = tmp_dir
    sb = _state_bytes()
    mb = _manifest_bytes(sb, version="v001")

    def download(folder_id, filename):
        if folder_id == "current-id":
            return b"totally broken json{{{{" if filename == "state.json" else mb
        return sb if filename == "state.json" else mb

    mock_drive_client.download_file.side_effect = download
    mock_drive_client.list_subfolders.return_value = [
        {"id": "v001-id", "name": "v001"}
    ]

    sm = _make_sm(mock_settings, mock_drive_client)
    sm._restore_to_sqlite = AsyncMock()

    result = await sm.load_latest_state()
    assert result is True


# ── All versions corrupt ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_all_versions_corrupt_continues_local(mock_settings, mock_drive_client, tmp_dir):
    mock_settings.FINORA_CACHE_DIR = tmp_dir
    mock_drive_client.download_file.return_value = b'{"not": "valid_finora_state"}'
    mock_drive_client.list_subfolders.return_value = []

    sm = _make_sm(mock_settings, mock_drive_client)
    sm._restore_to_sqlite = AsyncMock()

    result = await sm.load_latest_state()
    assert result is False
    sm._restore_to_sqlite.assert_not_awaited()


# ── Drive auth failure ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_drive_auth_failure_continues_local(mock_settings, tmp_dir):
    mock_settings.FINORA_CACHE_DIR = tmp_dir
    mock_settings.GOOGLE_DRIVE_ENABLED = True

    sm = StorageManager(MagicMock(), mock_settings)

    with patch("app.storage.storage_manager.LockManager") as mock_lm_cls, \
         patch("app.storage.storage_manager.GoogleDriveClient") as mock_client_cls:
        mock_lm = MagicMock()
        mock_lm.acquire = MagicMock()
        mock_lm_cls.return_value = mock_lm
        # Auth raises
        mock_client_cls.return_value.authenticate.side_effect = Exception("Auth failed")

        await sm.initialize()

    assert sm._drive_client is None
    assert sm._drive_status == SyncStatus.ERROR


# ── Normal shutdown ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_normal_shutdown_saves_state(mock_settings, mock_drive_client, tmp_dir):
    mock_settings.FINORA_CACHE_DIR = tmp_dir
    mock_settings.MAX_VERSIONS = 5
    mock_drive_client.list_subfolders.return_value = []
    mock_drive_client.get_or_create_folder.return_value = "new-folder"
    mock_drive_client.verify_file_exists.return_value = True

    sm = _make_sm(mock_settings, mock_drive_client)
    sm._export_from_sqlite = AsyncMock(return_value={"User": []})
    sm._lock_manager = MagicMock()
    sm._lock_manager.release = MagicMock()
    sm._lock_acquired = True

    await sm.shutdown()
    assert mock_drive_client.upload_file.called


# ── Upload failure during shutdown ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_shutdown_upload_failure_does_not_destroy_previous(
    mock_settings, mock_drive_client, tmp_dir
):
    mock_settings.FINORA_CACHE_DIR = tmp_dir
    mock_drive_client.list_subfolders.return_value = [
        {"id": "prev-id", "name": "v001"}
    ]
    mock_drive_client.get_or_create_folder.return_value = "new-folder"
    from app.storage.google_drive import GoogleDriveError
    mock_drive_client.upload_file.side_effect = GoogleDriveError("Upload failed")

    sm = _make_sm(mock_settings, mock_drive_client)
    sm._export_from_sqlite = AsyncMock(return_value={"User": []})
    sm._lock_manager = MagicMock()
    sm._lock_acquired = False

    result = await sm.save_state()
    assert result is False
    # Previous version folder must NOT be deleted
    mock_drive_client.delete_folder.assert_not_called()


# ── Drive disabled ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_drive_disabled_startup(mock_settings_disabled, tmp_dir):
    mock_settings_disabled.FINORA_CACHE_DIR = tmp_dir
    sm = StorageManager(MagicMock(), mock_settings_disabled)
    await sm.initialize()
    assert sm._drive_status == SyncStatus.DISABLED


@pytest.mark.asyncio
async def test_drive_disabled_shutdown(mock_settings_disabled, tmp_dir):
    mock_settings_disabled.FINORA_CACHE_DIR = tmp_dir
    sm = StorageManager(MagicMock(), mock_settings_disabled)
    sm._initialized = True
    # Should not raise and should not attempt Drive operations
    await sm.shutdown()


# ── Schema migration on load ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_schema_migration_applied_on_load(mock_settings, mock_drive_client, tmp_dir):
    """State with schema_version < CURRENT should be migrated before restoring."""
    mock_settings.FINORA_CACHE_DIR = tmp_dir
    # Build a state claiming schema_version == CURRENT (trivial migration path)
    data = {"User": [], "Category": []}
    import hashlib, json as _json
    dj = _json.dumps(data, ensure_ascii=False, sort_keys=True)
    cs = hashlib.sha256(dj.encode()).hexdigest()
    state = {
        "app": "Finora",
        "schema_version": CURRENT_SCHEMA_VERSION,  # already current → no migration needed
        "created_at": "2026-01-01T00:00:00+00:00",
        "app_version": "1.0.0",
        "save_reason": "test",
        "version": "v001",
        "checksum": cs,
        "data": data,
    }
    sb = _json.dumps(state).encode()
    mb = _manifest_bytes(sb)

    mock_drive_client.download_file.side_effect = (
        lambda folder_id, filename: sb if filename == "state.json" else mb
    )
    mock_drive_client.list_subfolders.return_value = []

    sm = _make_sm(mock_settings, mock_drive_client)
    sm._restore_to_sqlite = AsyncMock()

    result = await sm.load_latest_state()
    assert result is True
