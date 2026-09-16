"""lock_manager.py — Local file-based instance lock.

Prevents two simultaneously running Finora backend processes from
writing to the same Google Drive state and overwriting each other.

Implementation
--------------
Uses a PID-file lock stored in ``<FINORA_CACHE_DIR>/locks/instance.lock``.

Lock lifecycle:
    1. On startup, check if the lock file exists.
    2. If it exists, read the stored PID.
    3. If that PID is still running, warn and refuse to sync.
    4. If the PID is no longer running (stale lock), remove and re-acquire.
    5. Write the current PID to the lock file.
    6. On clean shutdown, remove the lock file.

Thread safety
-------------
This lock protects BETWEEN PROCESSES only.  Within a single process,
the StorageManager itself serialises Drive operations.

Important
---------
The lock prevents CONCURRENT WRITES.  If two instances are running
and the lock is held, the second instance will:

    - Start and serve the API normally (local SQLite)
    - Skip Drive synchronisation (startup and shutdown)
    - Log a clear warning

This is deliberately conservative: data loss from concurrent overwrites
is far worse than a missed sync in a second instance.
"""
from __future__ import annotations

import logging
import os
import signal

logger = logging.getLogger(__name__)


class InstanceLockError(Exception):
    """Raised when another live Finora instance already holds the lock."""


class LockManager:
    """File-based single-instance lock for Google Drive synchronisation.

    Args:
        cache_dir: Path to the ``.finora`` working directory.
    """

    def __init__(self, cache_dir: str) -> None:
        self.lock_dir = os.path.join(cache_dir, "locks")
        self.lock_file = os.path.join(self.lock_dir, "instance.lock")
        self._lock_held = False

    # ── Public interface ──────────────────────────────────────────────────────

    def acquire(self) -> None:
        """Acquire the instance lock.

        Raises:
            InstanceLockError: If another live Finora instance holds the lock.
        """
        os.makedirs(self.lock_dir, exist_ok=True)

        if os.path.exists(self.lock_file):
            existing_pid = self._read_pid()
            if existing_pid is not None and _pid_is_running(existing_pid):
                raise InstanceLockError(
                    f"Another Finora instance (PID {existing_pid}) is already running and "
                    "holds the Google Drive sync lock.\n"
                    "Only one instance can safely sync to Google Drive at a time.\n"
                    "Stop the other instance before starting a new one, or delete "
                    f"the lock file manually: {self.lock_file}"
                )
            else:
                logger.warning(
                    f"Stale lock file found (PID {existing_pid} is not running). "
                    "Removing stale lock and acquiring fresh lock."
                )
                self._remove_lock_file()

        self._write_pid()
        self._lock_held = True
        logger.info(f"Instance lock acquired (PID={os.getpid()}).")

    def release(self) -> None:
        """Release the instance lock (called on clean shutdown)."""
        if self._lock_held:
            self._remove_lock_file()
            self._lock_held = False
            logger.info("Instance lock released.")

    def is_held(self) -> bool:
        """Return True if THIS process currently holds the lock."""
        return self._lock_held

    # ── Private helpers ───────────────────────────────────────────────────────

    def _write_pid(self) -> None:
        with open(self.lock_file, "w") as fh:
            fh.write(str(os.getpid()))

    def _read_pid(self) -> int | None:
        try:
            with open(self.lock_file) as fh:
                return int(fh.read().strip())
        except (ValueError, OSError):
            return None

    def _remove_lock_file(self) -> None:
        try:
            os.remove(self.lock_file)
        except OSError:
            pass  # already gone


# ── Helper: cross-platform PID-alive check ────────────────────────────────────

def _pid_is_running(pid: int) -> bool:
    """Return True if *pid* refers to a currently running process."""
    if pid <= 0:
        return False
    import psutil
    try:
        return psutil.pid_exists(pid)
    except Exception:
        # Fallback if psutil fails for some reason
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False
