"""storage_manager.py — High-level Finora persistence orchestrator.

This is the SINGLE point of contact between Finora and the Google Drive
persistence layer.  The rest of the application (FastAPI routes, business
logic, SQLAlchemy models) never imports ``google_drive.py`` directly.

Public interface::

    sm = StorageManager(db_session_factory, settings)
    await sm.initialize()

    await sm.load_latest_state()   # startup: restore Drive state into SQLite
    await sm.save_state(reason)    # shutdown/manual: export SQLite → Drive
    await sm.autosave()            # periodic: export → update current/ only
    await sm.list_versions()       # → list of version labels
    await sm.restore_version(vid)  # recover a specific version
    sm.get_status()                # → SyncStatus dict

Orchestration guarantees
------------------------
    1. New version fully uploaded and verified BEFORE old version deleted.
    2. Corrupt state falls back to next newest valid version automatically.
    3. Autosave never creates numbered permanent versions.
    4. Version count never exceeds MAX_VERSIONS.
    5. Drive auth failure is surfaced clearly; local SQLite is NOT destroyed.
    6. All Drive calls happen inside asyncio.run_in_executor so the event
       loop is never blocked.

IMPORTANT: No trading logic. No business rules. Persistence only.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


# ── Sync status constants ─────────────────────────────────────────────────────
class SyncStatus:
    CONNECTED = "connected"
    SYNCING = "syncing"
    CURRENT = "current"
    OFFLINE = "offline"
    ERROR = "error"
    RECOVERY = "recovery"
    DISABLED = "disabled"


class StorageManager:
    """High-level persistence orchestrator.

    Args:
        db_session_factory: Callable that returns an ``AsyncSession`` context manager
                            (i.e. the ``AsyncSessionLocal`` from ``database.py``).
        settings:           The Pydantic ``Settings`` instance from ``config.py``.
    """

    def __init__(self, db_session_factory: Callable, settings: Any) -> None:
        self._db_factory = db_session_factory
        self._settings = settings

        self._drive_client: Optional[Any] = None  # GoogleDriveClient
        self._lock_manager: Optional[Any] = None  # LockManager
        self._root_folder_id: Optional[str] = None
        self._current_folder_id: Optional[str] = None
        self._versions_folder_id: Optional[str] = None

        self._drive_enabled: bool = settings.GOOGLE_DRIVE_ENABLED
        self._drive_status: str = SyncStatus.DISABLED if not self._drive_enabled else SyncStatus.OFFLINE
        self._last_sync: Optional[datetime] = None
        self._version_count: int = 0
        self._initialized: bool = False
        self._lock_acquired: bool = False

    # ── Initialization ────────────────────────────────────────────────────────

    async def initialize(self) -> None:
        """Initialize the storage layer. Must be called once on startup.

        If Drive is disabled, this is a no-op beyond creating local dirs.
        If Drive is enabled, authenticates and prepares folder structure.
        """
        # Always ensure local cache directories exist
        await self._run_sync(self._ensure_local_dirs)

        if not self._drive_enabled:
            logger.info("Google Drive persistence is DISABLED. Running local-only mode.")
            self._drive_status = SyncStatus.DISABLED
            self._initialized = True
            return

        # Acquire instance lock (prevents concurrent Drive writes)
        from app.storage.lock_manager import LockManager, InstanceLockError
        self._lock_manager = LockManager(self._settings.FINORA_CACHE_DIR)
        try:
            await self._run_sync(self._lock_manager.acquire)
            self._lock_acquired = True
        except InstanceLockError as exc:
            logger.warning(f"Instance lock not acquired: {exc}")
            # Fall back to local-only mode rather than crashing
            self._drive_enabled = False
            self._drive_status = SyncStatus.OFFLINE
            self._initialized = True
            return

        # Authenticate with Drive
        print("      Connecting to Google Drive...")
        try:
            from app.storage.google_drive import GoogleDriveClient, GoogleDriveError
            self._drive_client = GoogleDriveClient(
                credentials_file=self._settings.GOOGLE_CREDENTIALS_FILE,
                token_file=self._settings.GOOGLE_TOKEN_FILE,
            )
            await self._run_sync(self._drive_client.authenticate)
        except (FileNotFoundError, Exception) as exc:
            logger.error(f"Google Drive authentication failed: {exc}")
            self._drive_status = SyncStatus.ERROR
            self._drive_client = None
            self._initialized = True
            return

        # Ensure Drive folder structure
        try:
            await self._ensure_drive_folders()
            self._drive_status = SyncStatus.CONNECTED
        except Exception as exc:
            logger.error(f"Failed to prepare Drive folder structure: {exc}")
            self._drive_status = SyncStatus.ERROR

        self._initialized = True

    # ── Startup: Load latest state ────────────────────────────────────────────

    async def load_latest_state(self) -> bool:
        """Download the newest valid state from Drive and restore it into SQLite.

        Returns:
            True if state was successfully restored.
            False if Drive is disabled, no state found, or all versions corrupt.

        Recovery strategy:
            1. Try ``current/state.json`` first.
            2. Fall back to numbered versions from newest to oldest.
            3. If all are corrupt/missing, log a warning and continue with
               the existing local SQLite (never destroy local data).
        """
        if not self._drive_enabled or self._drive_client is None:
            logger.info("Drive disabled/unavailable — skipping state restore.")
            return False

        print("      Finding latest state...")
        self._drive_status = SyncStatus.SYNCING

        # Try current/ first, then version folders
        candidates = await self._get_restore_candidates()
        if not candidates:
            logger.info("No Finora state found in Google Drive.")
            self._drive_status = SyncStatus.CURRENT
            return False

        for label, folder_id in candidates:
            try:
                print(f"      Downloading state ({label})...")
                state_bytes, manifest = await self._download_version(folder_id)
                if state_bytes is None:
                    logger.warning(f"State not found in version {label}, skipping.")
                    continue

                print(f"      Validating state ({label})...")
                state = await self._validate_version(state_bytes, manifest)

                print(f"      Restoring state ({label}) into SQLite...")
                await self._restore_to_sqlite(state["data"])

                self._last_sync = datetime.now(timezone.utc)
                self._drive_status = SyncStatus.CURRENT
                logger.info(f"State restored successfully from {label}.")
                return True

            except Exception as exc:
                if label == "current":
                    logger.warning(f"Current Drive state is invalid ({exc}), trying versions...")
                else:
                    logger.warning(f"Version {label} is invalid ({exc}), trying next...")
                self._drive_status = SyncStatus.RECOVERY
                continue

        logger.warning(
            "All Drive state versions are corrupt or unreadable. "
            "Continuing with local SQLite data."
        )
        self._drive_status = SyncStatus.RECOVERY
        return False

    # ── Save state (permanent version) ───────────────────────────────────────

    async def save_state(self, reason: str = "manual") -> bool:
        """Export SQLite, create a permanent versioned backup, and upload to Drive.

        SAFE ORDER:
            1. Export from SQLite
            2. Validate locally
            3. Create new version folder
            4. Upload state.json
            5. Build and upload manifest (marked 'complete')
            6. Update current/
            7. Cleanup old versions (oldest LAST)

        Args:
            reason: Save reason string (``controlled_shutdown``, ``manual``, etc.)

        Returns:
            True on success, False if Drive is disabled or upload fails.
        """
        if not self._drive_enabled or self._drive_client is None:
            logger.info("Drive disabled/unavailable — skipping save.")
            return False

        self._drive_status = SyncStatus.SYNCING
        logger.info(f"Saving Finora state (reason={reason})...")

        # 1. Export from SQLite
        try:
            raw_data = await self._export_from_sqlite()
        except Exception as exc:
            logger.error(f"Failed to export state from SQLite: {exc}")
            self._drive_status = SyncStatus.ERROR
            return False

        # 2. Build envelope and validate
        from app.storage.state_serializer import (
            build_state_envelope, build_manifest,
            serialize_to_bytes, validate_state,
        )
        previous_version = await self._get_latest_version_label()
        next_version = await self._next_version_label()

        envelope = build_state_envelope(
            raw_data,
            save_reason=reason,
            version=next_version,
            app_version=self._settings.APP_VERSION,
        )
        try:
            validate_state(envelope)
        except Exception as exc:
            logger.error(f"Local state validation failed: {exc}")
            self._drive_status = SyncStatus.ERROR
            return False

        state_bytes = serialize_to_bytes(envelope)
        manifest = build_manifest(
            state_bytes,
            version=next_version,
            previous_version=previous_version,
            save_reason=reason,
            status="complete",
            app_version=self._settings.APP_VERSION,
        )
        manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode()

        # 3. Create new version folder
        print(f"      Creating version {next_version}...")
        try:
            version_folder_id = await self._run_sync(
                lambda: self._drive_client.get_or_create_folder(
                    next_version, self._versions_folder_id
                )
            )
        except Exception as exc:
            logger.error(f"Failed to create version folder {next_version}: {exc}")
            self._drive_status = SyncStatus.ERROR
            return False

        # 4 & 5. Upload state.json then manifest.json (manifest LAST as completion marker)
        print("      Uploading to Google Drive...")
        try:
            await self._run_sync(
                lambda: self._drive_client.upload_file(version_folder_id, "state.json", state_bytes)
            )
            await self._run_sync(
                lambda: self._drive_client.upload_file(version_folder_id, "manifest.json", manifest_bytes)
            )
        except Exception as exc:
            logger.error(f"Upload failed for version {next_version}: {exc}")
            self._drive_status = SyncStatus.ERROR
            # Previous good versions remain intact — do NOT clean up here
            return False

        # 6. Verify upload
        print("      Verifying upload...")
        if not await self._verify_upload(version_folder_id):
            logger.error(f"Upload verification failed for version {next_version}.")
            self._drive_status = SyncStatus.ERROR
            return False

        # 7. Update current/
        try:
            await self._update_current(state_bytes, manifest_bytes)
        except Exception as exc:
            logger.warning(f"Failed to update current/ state: {exc}")
            # Non-fatal: version is already saved

        # 8. Cleanup — ONLY after successful upload and verification
        await self._cleanup_old_versions()

        self._last_sync = datetime.now(timezone.utc)
        self._drive_status = SyncStatus.CURRENT
        self._version_count = await self._count_versions()
        logger.info(f"State saved successfully as {next_version}.")
        return True

    # ── Autosave (no new permanent version) ───────────────────────────────────

    async def autosave(self) -> bool:
        """Export current SQLite state and update ``current/`` on Drive.

        Does NOT create a new numbered version.
        Does NOT affect the permanent version count or rolling cleanup.

        Returns:
            True on success.
        """
        if not self._drive_enabled or self._drive_client is None:
            return False

        logger.debug("Autosave: exporting state...")
        try:
            raw_data = await self._export_from_sqlite()
        except Exception as exc:
            logger.error(f"Autosave export failed: {exc}")
            return False

        from app.storage.state_serializer import (
            build_state_envelope, build_manifest, serialize_to_bytes, validate_state
        )
        envelope = build_state_envelope(
            raw_data,
            save_reason="autosave",
            version="current",
            app_version=self._settings.APP_VERSION,
        )
        try:
            validate_state(envelope)
        except Exception as exc:
            logger.error(f"Autosave validation failed: {exc}")
            return False

        state_bytes = serialize_to_bytes(envelope)
        manifest = build_manifest(
            state_bytes,
            version="current",
            save_reason="autosave",
            status="complete",
            app_version=self._settings.APP_VERSION,
        )
        manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode()

        try:
            await self._update_current(state_bytes, manifest_bytes)
            self._last_sync = datetime.now(timezone.utc)
            logger.debug("Autosave complete.")
            return True
        except Exception as exc:
            logger.error(f"Autosave upload failed: {exc}")
            return False

    # ── Version management ────────────────────────────────────────────────────

    async def list_versions(self) -> list[str]:
        """Return a sorted list of version labels stored in Drive.

        Returns:
            e.g. ``["v001", "v002", "v003"]``
        """
        if not self._drive_enabled or self._drive_client is None:
            return []
        try:
            folders = await self._run_sync(
                lambda: self._drive_client.list_subfolders(self._versions_folder_id)
            )
            labels = sorted(f["name"] for f in folders if f["name"].startswith("v"))
            return labels
        except Exception as exc:
            logger.error(f"Failed to list versions: {exc}")
            return []

    async def restore_version(self, version_id: str) -> bool:
        """Restore a specific numbered version from Drive into SQLite.

        Args:
            version_id: Version label, e.g. ``"v003"``.

        Returns:
            True if successfully restored.
        """
        if not self._drive_enabled or self._drive_client is None:
            return False
        folders = await self._run_sync(
            lambda: self._drive_client.list_subfolders(self._versions_folder_id)
        )
        folder_map = {f["name"]: f["id"] for f in folders}
        folder_id = folder_map.get(version_id)
        if not folder_id:
            logger.error(f"Version {version_id} not found in Drive.")
            return False

        try:
            state_bytes, manifest = await self._download_version(folder_id)
            state = await self._validate_version(state_bytes, manifest)
            await self._restore_to_sqlite(state["data"])
            logger.info(f"Manually restored version {version_id}.")
            return True
        except Exception as exc:
            logger.error(f"Failed to restore version {version_id}: {exc}")
            return False

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self) -> dict:
        """Return a dict representing the current sync status."""
        return {
            "google_drive": self._drive_status,
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "local_state": "current",
            "cloud_state": self._drive_status,
            "versions": self._version_count,
            "max_versions": self._settings.MAX_VERSIONS,
            "drive_enabled": self._drive_enabled,
        }

    # ── Teardown ──────────────────────────────────────────────────────────────

    async def shutdown(self) -> None:
        """Called during controlled shutdown. Saves state and releases the lock."""
        if self._drive_enabled and self._drive_client is not None:
            await self.save_state(reason="controlled_shutdown")
        if self._lock_manager and self._lock_acquired:
            await self._run_sync(self._lock_manager.release)

    # ── Internal: Drive folder setup ──────────────────────────────────────────

    async def _ensure_drive_folders(self) -> None:
        """Create the Finora/ folder tree on Drive if not already present."""
        root = self._settings.GOOGLE_DRIVE_ROOT
        self._root_folder_id = await self._run_sync(
            lambda: self._drive_client.get_or_create_folder(root)
        )
        self._current_folder_id = await self._run_sync(
            lambda: self._drive_client.get_or_create_folder("current", self._root_folder_id)
        )
        self._versions_folder_id = await self._run_sync(
            lambda: self._drive_client.get_or_create_folder("versions", self._root_folder_id)
        )
        # logs/ folder (optional, for future use)
        await self._run_sync(
            lambda: self._drive_client.get_or_create_folder("logs", self._root_folder_id)
        )

    # ── Internal: Export / Restore SQLite ────────────────────────────────────

    async def _export_from_sqlite(self) -> dict:
        """Export all Finora data from SQLite using backup_service."""
        from app.services.backup_service import export_user_data
        from app.models.user import User
        from sqlalchemy import select

        all_data: dict = {}
        async with self._db_factory() as db:
            # Export every user's data
            result = await db.execute(select(User))
            users = result.scalars().all()
            for user in users:
                user_export = await export_user_data(db, user.id)
                # Merge into all_data, keyed by model name
                for model_name, rows in user_export.items():
                    if model_name not in all_data:
                        all_data[model_name] = []
                    all_data[model_name].extend(rows)

        return all_data

    async def _restore_to_sqlite(self, data: dict) -> None:
        """Restore exported data back into SQLite using backup_service."""
        from app.services.backup_service import restore_user_data
        from app.models.user import User
        from sqlalchemy import select

        # backup_service.restore_user_data works per user_id.
        # We reconstruct the per-user dicts from the merged data.
        import uuid as _uuid

        async with self._db_factory() as db:
            result = await db.execute(select(User))
            users = result.scalars().all()

            for user in users:
                user_id_str = str(user.id)
                # Build per-user slice of the backup data
                user_data = self._slice_user_data(data, user_id_str)
                await restore_user_data(db, user.id, user_data)
            await db.commit()

    def _slice_user_data(self, all_data: dict, user_id_str: str) -> dict:
        """Filter ``all_data`` to rows belonging to ``user_id_str``."""
        sliced: dict = {}
        for model_name, rows in all_data.items():
            if not isinstance(rows, list):
                sliced[model_name] = rows
                continue
            filtered = [
                row for row in rows
                if row.get("user_id") == user_id_str
                # User row itself has 'id' not 'user_id'
                or row.get("id") == user_id_str
            ]
            sliced[model_name] = filtered
        return sliced

    # ── Internal: Version helpers ─────────────────────────────────────────────

    async def _get_restore_candidates(self) -> list[tuple[str, str]]:
        """Return [(label, folder_id)] ordered from newest to oldest to try."""
        candidates = []

        # 1. current/
        if self._current_folder_id:
            candidates.append(("current", self._current_folder_id))

        # 2. Numbered versions (newest first)
        versions = await self.list_versions()
        for label in reversed(versions):
            folders = await self._run_sync(
                lambda l=label: self._drive_client.list_subfolders(self._versions_folder_id)
            )
            folder_map = {f["name"]: f["id"] for f in folders}
            if label in folder_map:
                candidates.append((label, folder_map[label]))

        return candidates

    async def _download_version(self, folder_id: str) -> tuple[Optional[bytes], Optional[dict]]:
        """Download state.json and manifest.json from a folder."""
        state_bytes: Optional[bytes] = await self._run_sync(
            lambda: self._drive_client.download_file(folder_id, "state.json")
        )
        manifest_bytes: Optional[bytes] = await self._run_sync(
            lambda: self._drive_client.download_file(folder_id, "manifest.json")
        )
        manifest: Optional[dict] = None
        if manifest_bytes:
            try:
                manifest = json.loads(manifest_bytes.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                logger.warning(f"Failed to parse manifest.json: {exc}")
        return state_bytes, manifest

    async def _validate_version(
        self, state_bytes: Optional[bytes], manifest: Optional[dict]
    ) -> dict:
        """Validate and return the parsed state dict.

        Raises:
            ValueError: On any validation failure.
        """
        from app.storage.state_serializer import (
            deserialize_from_bytes, validate_state, validate_manifest, migrate_state,
            StateValidationError,
        )

        if not state_bytes:
            raise ValueError("state.json is missing or empty.")

        # If manifest exists, validate it first (quick check)
        if manifest:
            try:
                validate_manifest(manifest, state_bytes)
            except StateValidationError as exc:
                raise ValueError(str(exc)) from exc

        state = deserialize_from_bytes(state_bytes)

        # Apply schema migrations if needed
        state = migrate_state(state)

        # Validate envelope checksum
        try:
            validate_state(state)
        except StateValidationError as exc:
            raise ValueError(str(exc)) from exc

        return state

    async def _next_version_label(self) -> str:
        """Return the next sequential version label (e.g. ``v006``)."""
        versions = await self.list_versions()
        if not versions:
            return "v001"
        latest = versions[-1]  # e.g. "v005"
        try:
            n = int(latest[1:]) + 1
        except (ValueError, IndexError):
            n = len(versions) + 1
        return f"v{n:03d}"

    async def _get_latest_version_label(self) -> str:
        """Return the label of the most recent version, or empty string."""
        versions = await self.list_versions()
        return versions[-1] if versions else ""

    async def _verify_upload(self, folder_id: str) -> bool:
        """Verify that both state.json and manifest.json exist in *folder_id*."""
        try:
            state_ok = await self._run_sync(
                lambda: self._drive_client.verify_file_exists(folder_id, "state.json")
            )
            manifest_ok = await self._run_sync(
                lambda: self._drive_client.verify_file_exists(folder_id, "manifest.json")
            )
            return state_ok and manifest_ok
        except Exception as exc:
            logger.error(f"Upload verification error: {exc}")
            return False

    async def _update_current(self, state_bytes: bytes, manifest_bytes: bytes) -> None:
        """Overwrite current/state.json and current/manifest.json."""
        await self._run_sync(
            lambda: self._drive_client.upload_file(
                self._current_folder_id, "state.json", state_bytes
            )
        )
        await self._run_sync(
            lambda: self._drive_client.upload_file(
                self._current_folder_id, "manifest.json", manifest_bytes
            )
        )

    async def _cleanup_old_versions(self) -> None:
        """Delete oldest versions until count ≤ MAX_VERSIONS.

        SAFE: only called AFTER the new version is confirmed valid.
        """
        max_v = self._settings.MAX_VERSIONS
        versions = await self.list_versions()
        if len(versions) <= max_v:
            return

        to_delete = versions[: len(versions) - max_v]
        folders = await self._run_sync(
            lambda: self._drive_client.list_subfolders(self._versions_folder_id)
        )
        folder_map = {f["name"]: f["id"] for f in folders}

        for label in to_delete:
            fid = folder_map.get(label)
            if fid:
                try:
                    await self._run_sync(lambda fid=fid: self._drive_client.delete_folder(fid))
                    logger.info(f"Deleted old version {label}.")
                    print(f"      Cleaned up old version {label}.")
                except Exception as exc:
                    logger.warning(f"Failed to delete version {label}: {exc}")

    async def _count_versions(self) -> int:
        versions = await self.list_versions()
        return len(versions)

    # ── Internal: Local dirs ──────────────────────────────────────────────────

    def _ensure_local_dirs(self) -> None:
        base = self._settings.FINORA_CACHE_DIR
        for subdir in ("cache", "state", "temp", "locks", "logs"):
            os.makedirs(os.path.join(base, subdir), exist_ok=True)

    # ── Async helper ──────────────────────────────────────────────────────────

    @staticmethod
    async def _run_sync(fn: Callable) -> Any:
        """Run a synchronous callable in a thread pool executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, fn)
