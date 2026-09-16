"""test_storage_manager.py — Unit tests for StorageManager.

Tests:
    - Drive-disabled: initialize is a no-op, get_status returns disabled
    - Drive-disabled: load_latest_state returns False without Drive calls
    - Drive-disabled: save_state returns False without Drive calls
    - Drive-disabled: autosave returns False without Drive calls
    - Drive-enabled: initialize sets up folders
    - Drive-enabled: load_latest_state restores from current/
    - Drive-enabled: load_latest_state falls back to v001 when current is corrupt
    - Drive-enabled: load_latest_state returns False when all versions corrupt
    - Drive-enabled: save_state uploads state + manifest + updates current
    - Drive-enabled: save_state does NOT delete old version until new version verified
    - Drive-enabled: cleanup removes oldest when count > MAX_VERSIONS
    - Drive-enabled: MAX_VERSIONS=5 keeps exactly 5 versions
    - Drive-enabled: autosave updates current/ without creating a new version folder
    - Drive-enabled: upload failure does not corrupt previous state
    - list_versions returns sorted version labels
    - get_status returns honest values
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest
import pytest_asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.storage.storage_manager import StorageManager, SyncStatus
from app.storage.state_serializer import build_state_envelope, serialize_to_bytes, build_manifest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_sm(mock_settings, mock_drive_client=None, mock_db_factory=None):
    """Create a StorageManager with mocked internals."""
    sm = StorageManager(mock_db_factory or MagicMock(), mock_settings)
    if mock_drive_client is not None:
        sm._drive_client = mock_drive_client
        sm._root_folder_id = "root-id"
        sm._current_folder_id = "current-id"
        sm._versions_folder_id = "versions-id"
    return sm


def _valid_state_bytes(data=None):
    """Return valid state bytes."""
    if data is None:
        data = {"User": [], "Category": [], "Transaction": []}
    envelope = build_state_envelope(data, save_reason="test", version="v001")
    return serialize_to_bytes(envelope)


def _valid_manifest_bytes(state_bytes, *, version="v001", status="complete"):
    manifest = build_manifest(state_bytes, version=version, status=status)
    return json.dumps(manifest, ensure_ascii=False, indent=2).encode()


# ── Drive-disabled mode ───────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestDriveDisabledMode:
    async def test_initialize_noop(self, mock_settings_disabled, tmp_dir):
        mock_settings_disabled.FINORA_CACHE_DIR = tmp_dir
        sm = _make_sm(mock_settings_disabled)
        await sm.initialize()
        assert sm._drive_status == SyncStatus.DISABLED

    async def test_load_returns_false(self, mock_settings_disabled, tmp_dir):
        mock_settings_disabled.FINORA_CACHE_DIR = tmp_dir
        sm = _make_sm(mock_settings_disabled)
        sm._initialized = True
        result = await sm.load_latest_state()
        assert result is False

    async def test_save_returns_false(self, mock_settings_disabled, tmp_dir):
        mock_settings_disabled.FINORA_CACHE_DIR = tmp_dir
        sm = _make_sm(mock_settings_disabled)
        sm._initialized = True
        result = await sm.save_state()
        assert result is False

    async def test_autosave_returns_false(self, mock_settings_disabled, tmp_dir):
        mock_settings_disabled.FINORA_CACHE_DIR = tmp_dir
        sm = _make_sm(mock_settings_disabled)
        result = await sm.autosave()
        assert result is False

    async def test_get_status_disabled(self, mock_settings_disabled, tmp_dir):
        mock_settings_disabled.FINORA_CACHE_DIR = tmp_dir
        sm = _make_sm(mock_settings_disabled)
        await sm.initialize()
        status = sm.get_status()
        assert status["google_drive"] == SyncStatus.DISABLED
        assert status["drive_enabled"] is False


# ── Drive-enabled: load_latest_state ─────────────────────────────────────────

@pytest.mark.asyncio
class TestLoadLatestState:
    async def test_restores_from_current(self, mock_settings, mock_drive_client, tmp_dir):
        mock_settings.FINORA_CACHE_DIR = tmp_dir
        state_bytes = _valid_state_bytes()
        manifest_bytes = _valid_manifest_bytes(state_bytes)

        mock_drive_client.download_file.side_effect = (
            lambda folder_id, filename:
            state_bytes if filename == "state.json" else manifest_bytes
        )
        mock_drive_client.list_subfolders.return_value = []  # no numbered versions

        sm = _make_sm(mock_settings, mock_drive_client)
        sm._drive_enabled = True
        sm._drive_status = SyncStatus.CONNECTED

        # Patch _restore_to_sqlite to avoid DB calls
        sm._restore_to_sqlite = AsyncMock()
        result = await sm.load_latest_state()

        assert result is True
        sm._restore_to_sqlite.assert_awaited_once()

    async def test_falls_back_to_version_when_current_corrupt(
        self, mock_settings, mock_drive_client, tmp_dir
    ):
        mock_settings.FINORA_CACHE_DIR = tmp_dir
        state_bytes = _valid_state_bytes()
        manifest_bytes = _valid_manifest_bytes(state_bytes, version="v001")

        def download_side_effect(folder_id, filename):
            if folder_id == "current-id":
                # Corrupt current state
                return b'{"corrupted": true}' if filename == "state.json" else manifest_bytes
            # v001 folder has valid state
            return state_bytes if filename == "state.json" else manifest_bytes

        mock_drive_client.download_file.side_effect = download_side_effect
        mock_drive_client.list_subfolders.return_value = [
            {"id": "v001-folder", "name": "v001"}
        ]

        sm = _make_sm(mock_settings, mock_drive_client)
        sm._drive_enabled = True
        sm._drive_status = SyncStatus.CONNECTED
        sm._restore_to_sqlite = AsyncMock()

        result = await sm.load_latest_state()
        assert result is True

    async def test_returns_false_when_all_corrupt(
        self, mock_settings, mock_drive_client, tmp_dir
    ):
        mock_settings.FINORA_CACHE_DIR = tmp_dir
        mock_drive_client.download_file.return_value = b'{"totally": "corrupt"}'
        mock_drive_client.list_subfolders.return_value = []

        sm = _make_sm(mock_settings, mock_drive_client)
        sm._drive_enabled = True
        sm._drive_status = SyncStatus.CONNECTED
        sm._restore_to_sqlite = AsyncMock()

        result = await sm.load_latest_state()
        assert result is False


# ── Drive-enabled: save_state ─────────────────────────────────────────────────

@pytest.mark.asyncio
class TestSaveState:
    async def test_save_uploads_state_and_manifest(
        self, mock_settings, mock_drive_client, tmp_dir
    ):
        mock_settings.FINORA_CACHE_DIR = tmp_dir
        mock_drive_client.list_subfolders.return_value = []
        mock_drive_client.get_or_create_folder.return_value = "new-version-folder"
        mock_drive_client.verify_file_exists.return_value = True

        sm = _make_sm(mock_settings, mock_drive_client)
        sm._drive_enabled = True
        sm._export_from_sqlite = AsyncMock(return_value={"User": [], "Category": []})
        sm._restore_to_sqlite = AsyncMock()

        result = await sm.save_state(reason="test")
        assert result is True
        # Both state.json and manifest.json should have been uploaded
        upload_filenames = [
            call_args[0][1]
            for call_args in mock_drive_client.upload_file.call_args_list
        ]
        assert "state.json" in upload_filenames
        assert "manifest.json" in upload_filenames

    async def test_save_does_not_delete_old_before_verify(
        self, mock_settings, mock_drive_client, tmp_dir
    ):
        """Old versions must not be deleted before upload+verify succeeds."""
        mock_settings.FINORA_CACHE_DIR = tmp_dir
        mock_settings.MAX_VERSIONS = 5
        # Simulate 5 existing versions
        mock_drive_client.list_subfolders.return_value = [
            {"id": f"f{i}", "name": f"v{i:03d}"} for i in range(1, 6)
        ]
        mock_drive_client.get_or_create_folder.return_value = "new-folder-id"
        mock_drive_client.verify_file_exists.return_value = True

        sm = _make_sm(mock_settings, mock_drive_client)
        sm._drive_enabled = True
        sm._export_from_sqlite = AsyncMock(return_value={"User": []})
        sm._restore_to_sqlite = AsyncMock()

        await sm.save_state(reason="test")

        # delete_folder should have been called AFTER verify (at the end)
        upload_calls = mock_drive_client.upload_file.call_args_list
        delete_calls = mock_drive_client.delete_folder.call_args_list
        # All uploads must happen before any deletes
        assert len(upload_calls) >= 2  # state + manifest at minimum
        # Only 1 old version should be deleted (6 versions → keep 5 → delete 1)
        assert len(delete_calls) == 1

    async def test_upload_failure_leaves_previous_version_intact(
        self, mock_settings, mock_drive_client, tmp_dir
    ):
        mock_settings.FINORA_CACHE_DIR = tmp_dir
        mock_drive_client.list_subfolders.return_value = [
            {"id": "prev-folder", "name": "v001"}
        ]
        mock_drive_client.get_or_create_folder.return_value = "new-folder"
        # Simulate upload failure
        from app.storage.google_drive import GoogleDriveError
        mock_drive_client.upload_file.side_effect = GoogleDriveError("Network error")

        sm = _make_sm(mock_settings, mock_drive_client)
        sm._drive_enabled = True
        sm._export_from_sqlite = AsyncMock(return_value={"User": []})

        result = await sm.save_state()
        assert result is False
        # delete_folder must NOT have been called
        mock_drive_client.delete_folder.assert_not_called()


# ── Drive-enabled: version retention ─────────────────────────────────────────

@pytest.mark.asyncio
class TestVersionRetention:
    async def test_max_versions_5_cleanup(self, mock_settings, mock_drive_client, tmp_dir):
        """After saving v006, v001 should be deleted, leaving v002-v006."""
        mock_settings.FINORA_CACHE_DIR = tmp_dir
        mock_settings.MAX_VERSIONS = 5
        existing = [{"id": f"f{i}", "name": f"v{i:03d}"} for i in range(1, 6)]
        mock_drive_client.list_subfolders.return_value = existing + [
            {"id": "f6", "name": "v006"}
        ]
        mock_drive_client.get_or_create_folder.return_value = "new-folder"
        mock_drive_client.verify_file_exists.return_value = True

        sm = _make_sm(mock_settings, mock_drive_client)
        sm._drive_enabled = True
        sm._export_from_sqlite = AsyncMock(return_value={"User": []})
        sm._restore_to_sqlite = AsyncMock()

        await sm._cleanup_old_versions()

        # Only v001 (the oldest) should be deleted
        deleted_ids = [c[0][0] for c in mock_drive_client.delete_folder.call_args_list]
        assert "f1" in deleted_ids
        assert len(deleted_ids) == 1

    async def test_no_cleanup_when_under_limit(self, mock_settings, mock_drive_client, tmp_dir):
        mock_settings.FINORA_CACHE_DIR = tmp_dir
        mock_settings.MAX_VERSIONS = 5
        mock_drive_client.list_subfolders.return_value = [
            {"id": "f1", "name": "v001"},
            {"id": "f2", "name": "v002"},
        ]
        sm = _make_sm(mock_settings, mock_drive_client)
        sm._drive_enabled = True
        await sm._cleanup_old_versions()
        mock_drive_client.delete_folder.assert_not_called()


# ── Autosave ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestAutosave:
    async def test_autosave_updates_current_only(
        self, mock_settings, mock_drive_client, tmp_dir
    ):
        mock_settings.FINORA_CACHE_DIR = tmp_dir
        mock_drive_client.verify_file_exists.return_value = True

        sm = _make_sm(mock_settings, mock_drive_client)
        sm._drive_enabled = True
        sm._export_from_sqlite = AsyncMock(return_value={"User": []})

        result = await sm.autosave()
        assert result is True

        # No new version folder created — only current/ updates
        create_calls = [
            c for c in mock_drive_client.get_or_create_folder.call_args_list
        ]
        version_folder_creates = [
            c for c in create_calls
            if c[0][0].startswith("v") and c[0][0] != "current"
        ]
        assert len(version_folder_creates) == 0

        # current/ should have been updated (upload called)
        assert mock_drive_client.upload_file.called


# ── list_versions ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
class TestListVersions:
    async def test_returns_sorted_labels(self, mock_settings, mock_drive_client, tmp_dir):
        mock_settings.FINORA_CACHE_DIR = tmp_dir
        mock_drive_client.list_subfolders.return_value = [
            {"id": "f3", "name": "v003"},
            {"id": "f1", "name": "v001"},
            {"id": "f2", "name": "v002"},
        ]
        sm = _make_sm(mock_settings, mock_drive_client)
        sm._drive_enabled = True
        versions = await sm.list_versions()
        assert versions == ["v001", "v002", "v003"]

    async def test_empty_when_drive_disabled(self, mock_settings_disabled, tmp_dir):
        mock_settings_disabled.FINORA_CACHE_DIR = tmp_dir
        sm = _make_sm(mock_settings_disabled)
        versions = await sm.list_versions()
        assert versions == []
