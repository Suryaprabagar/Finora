"""test_autosave.py — Unit tests for the AutosaveTask background task.

Tests:
    - start() creates a running asyncio task
    - stop() cancels the task
    - _do_autosave calls storage_manager.autosave()
    - autosave failure does not propagate (error isolation)
    - task does not autosave immediately on start (waits first interval)
    - multiple start() calls do not create duplicate tasks
"""
from __future__ import annotations

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.storage.autosave import AutosaveTask


class TestAutosaveTask:
    def _make_task(self, interval=300):
        sm = MagicMock()
        sm.autosave = AsyncMock(return_value=True)
        return AutosaveTask(sm, interval_seconds=interval), sm

    @pytest.mark.asyncio
    async def test_start_creates_task(self):
        task, sm = self._make_task()
        task.start()
        assert task._task is not None
        assert not task._task.done()
        task.stop()

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self):
        task, sm = self._make_task()
        task.start()
        task.stop()
        # Give the event loop a tick to process cancellation
        await asyncio.sleep(0)
        assert not task._running

    @pytest.mark.asyncio
    async def test_multiple_start_does_not_duplicate(self):
        task, sm = self._make_task()
        task.start()
        first_task = task._task
        task.start()  # second call should be no-op
        assert task._task is first_task
        task.stop()

    @pytest.mark.asyncio
    async def test_do_autosave_calls_manager(self):
        task, sm = self._make_task()
        await task._do_autosave()
        sm.autosave.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_autosave_failure_does_not_propagate(self):
        task, sm = self._make_task()
        sm.autosave.side_effect = RuntimeError("Drive down")
        # Should not raise
        await task._do_autosave()

    @pytest.mark.asyncio
    async def test_does_not_autosave_before_first_interval(self):
        """The task sleeps FIRST before the initial save."""
        task, sm = self._make_task(interval=9999)
        task.start()
        await asyncio.sleep(0.05)  # tiny tick — not enough to trigger first save
        sm.autosave.assert_not_awaited()
        task.stop()
