"""conftest.py — Shared fixtures for storage tests.

All fixtures here mock Google Drive so tests never require a real
Google account or network connection.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Path setup ────────────────────────────────────────────────────────────────
# Ensure the backend/ directory is on the path so imports work when running
# pytest from the backend/ directory.
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_state_envelope(data: dict | None = None, *, checksum_ok: bool = True) -> dict:
    """Build a valid state envelope dict for testing."""
    if data is None:
        data = {"User": [], "Transaction": [], "Category": []}
    data_json = json.dumps(data, ensure_ascii=False, sort_keys=True)
    checksum = hashlib.sha256(data_json.encode()).hexdigest()
    if not checksum_ok:
        checksum = "bad" + checksum[3:]  # deliberately corrupt
    return {
        "app": "Finora",
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "app_version": "1.0.0",
        "save_reason": "test",
        "version": "v001",
        "checksum": checksum,
        "data": data,
    }


def make_manifest(state_bytes: bytes, *, version: str = "v001", status: str = "complete") -> dict:
    """Build a valid manifest dict for testing."""
    sha256 = hashlib.sha256(state_bytes).hexdigest()
    return {
        "version": version,
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "app_version": "1.0.0",
        "previous_version": "",
        "status": status,
        "save_reason": "test",
        "files": {
            "state.json": {
                "size": len(state_bytes),
                "sha256": sha256,
            }
        },
    }


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_dir():
    """Return a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def sample_data():
    """Minimal valid Finora export data dict."""
    uid = str(uuid.uuid4())
    return {
        "User": [{"id": uid, "email": "test@finora.app", "full_name": "Test User"}],
        "Category": [],
        "Transaction": [],
    }


@pytest.fixture
def sample_envelope(sample_data):
    """A valid state envelope wrapping sample_data."""
    return make_state_envelope(sample_data)


@pytest.fixture
def sample_envelope_bytes(sample_envelope):
    """JSON bytes of sample_envelope."""
    return json.dumps(sample_envelope, ensure_ascii=False, indent=2).encode("utf-8")


@pytest.fixture
def sample_manifest(sample_envelope_bytes):
    """A valid manifest for sample_envelope_bytes."""
    return make_manifest(sample_envelope_bytes)


@pytest.fixture
def mock_drive_client():
    """A MagicMock mimicking GoogleDriveClient for unit tests."""
    client = MagicMock()
    client.authenticate = MagicMock()

    # Folder operations
    client.get_or_create_folder = MagicMock(side_effect=lambda name, parent=None: f"folder-{name}")
    client.list_subfolders = MagicMock(return_value=[])
    client.list_files = MagicMock(return_value=[])

    # File operations
    client.upload_file = MagicMock(return_value="file-id-123")
    client.download_file = MagicMock(return_value=None)
    client.delete_folder = MagicMock()
    client.verify_file_exists = MagicMock(return_value=True)
    client._find_file = MagicMock(return_value=None)

    return client


@pytest.fixture
def mock_settings(tmp_dir):
    """A MagicMock Settings object with sensible test defaults."""
    s = MagicMock()
    s.GOOGLE_DRIVE_ENABLED = True
    s.GOOGLE_DRIVE_ROOT = "Finora"
    s.GOOGLE_CREDENTIALS_FILE = os.path.join(tmp_dir, "credentials.json")
    s.GOOGLE_TOKEN_FILE = os.path.join(tmp_dir, ".finora", "token.json")
    s.MAX_VERSIONS = 5
    s.AUTOSAVE_INTERVAL = 300
    s.FINORA_CACHE_DIR = os.path.join(tmp_dir, ".finora")
    s.APP_VERSION = "1.0.0"
    return s


@pytest.fixture
def mock_settings_disabled(mock_settings):
    """Settings with Drive disabled."""
    mock_settings.GOOGLE_DRIVE_ENABLED = False
    return mock_settings


@pytest.fixture
def mock_db_factory(sample_data):
    """A fake async session factory that returns sample data on export."""
    # We won't actually call db in most storage unit tests; provide a stub.
    factory = MagicMock()
    return factory
