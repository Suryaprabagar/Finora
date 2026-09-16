"""autosave.py — Background autosave task for Finora.

Runs as an asyncio background task started during FastAPI lifespan.

Behaviour:
    Every AUTOSAVE_INTERVAL seconds (default 300 = 5 minutes):

        SQLite
          ↓
        StorageManager.autosave()
          ↓
        export + validate
          ↓
        upload/update current/state.json
          ↓
        update current/manifest.json

This does NOT create a new permanent numbered version.
Permanent versions are only created on controlled shutdown or manual sync.

Error handling:
    - Autosave failures are logged but do NOT crash the application.
    - The next autosave tick will retry.
    - Failed autosaves do NOT affect the last known-good Drive state.

IMPORTANT:
    Never block the main event loop. The StorageManager already offloads
    Drive I/O to a thread pool executor.
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.storage.storage_manager import StorageManager

logger = logging.getLogger(__name__)


class AutosaveTask:
    """Manages the background autosave asyncio task.

    Args:
        storage_manager: Initialized StorageManager instance.
        interval_seconds: How often to run autosave (default 300s).
    """

    def __init__(self, storage_manager: "StorageManager", interval_seconds: int = 300) -> None:
        self._storage_manager = storage_manager
        self._interval = interval_seconds
        self._task: asyncio.Task | None = None
        self._running = False

    def start(self) -> None:
        """Start the background autosave task."""
        if self._task is not None and not self._task.done():
            logger.warning("Autosave task is already running.")
            return
        self._running = True
        self._task = asyncio.create_task(self._loop(), name="finora-autosave")
        logger.info(f"Autosave task started (interval={self._interval}s).")

    def stop(self) -> None:
        """Stop the background autosave task gracefully."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Autosave task stopped.")

    async def _loop(self) -> None:
        """Main autosave loop: sleep → autosave → repeat."""
        logger.debug(f"Autosave loop starting (interval={self._interval}s).")
        try:
            while self._running:
                # Wait first, then save. This avoids an immediate autosave
                # right after startup (which just completed a full load).
                await asyncio.sleep(self._interval)
                if not self._running:
                    break
                await self._do_autosave()
        except asyncio.CancelledError:
            logger.debug("Autosave task cancelled.")
        except Exception as exc:
            logger.error(f"Unexpected error in autosave loop: {exc}", exc_info=True)

    async def _do_autosave(self) -> None:
        """Execute a single autosave cycle with error isolation."""
        try:
            logger.debug("Autosave triggered.")
            success = await self._storage_manager.autosave()
            if success:
                logger.info("Autosave completed successfully.")
            else:
                logger.debug("Autosave skipped (Drive disabled or unavailable).")
        except Exception as exc:
            logger.error(f"Autosave failed: {exc}", exc_info=True)
            # Do not re-raise — a failed autosave must not crash the app.
