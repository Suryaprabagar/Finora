"""test_lock_manager.py — Unit tests for lock_manager.py.

Tests:
    - acquire creates lock file with PID
    - acquire releases lock on release()
    - stale lock (dead PID) is removed and re-acquired
    - live PID raises InstanceLockError
    - is_held() reflects state
    - release() is idempotent (no error if already released)
    - _pid_is_running returns False for PID 0 / negative
"""
from __future__ import annotations

import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.storage.lock_manager import LockManager, InstanceLockError, _pid_is_running


class TestLockManager:
    def test_acquire_creates_lock_file(self, tmp_dir):
        lm = LockManager(tmp_dir)
        lm.acquire()
        assert os.path.exists(lm.lock_file)
        lm.release()

    def test_acquire_writes_current_pid(self, tmp_dir):
        lm = LockManager(tmp_dir)
        lm.acquire()
        with open(lm.lock_file) as f:
            pid = int(f.read().strip())
        assert pid == os.getpid()
        lm.release()

    def test_release_removes_lock_file(self, tmp_dir):
        lm = LockManager(tmp_dir)
        lm.acquire()
        lm.release()
        assert not os.path.exists(lm.lock_file)

    def test_is_held_true_after_acquire(self, tmp_dir):
        lm = LockManager(tmp_dir)
        lm.acquire()
        assert lm.is_held() is True
        lm.release()

    def test_is_held_false_after_release(self, tmp_dir):
        lm = LockManager(tmp_dir)
        lm.acquire()
        lm.release()
        assert lm.is_held() is False

    def test_stale_lock_is_cleared(self, tmp_dir):
        lm = LockManager(tmp_dir)
        os.makedirs(lm.lock_dir, exist_ok=True)
        # Write a PID that cannot possibly be running (PID 1 exists on Linux but
        # we write an implausibly large PID that cannot belong to a running process)
        with open(lm.lock_file, "w") as f:
            f.write("99999999")  # almost certainly not running
        # Acquire should succeed by clearing the stale lock
        lm.acquire()
        assert lm.is_held()
        lm.release()

    def test_live_instance_raises(self, tmp_dir):
        """Simulate another live instance holding the lock."""
        lm1 = LockManager(tmp_dir)
        lm1.acquire()
        # Second manager pointing at the same dir
        lm2 = LockManager(tmp_dir)
        with pytest.raises(InstanceLockError):
            lm2.acquire()
        lm1.release()

    def test_release_is_idempotent(self, tmp_dir):
        lm = LockManager(tmp_dir)
        lm.acquire()
        lm.release()
        lm.release()  # should not raise

    def test_pid_is_running_current_process(self):
        assert _pid_is_running(os.getpid()) is True

    def test_pid_is_running_zero(self):
        assert _pid_is_running(0) is False

    def test_pid_is_running_negative(self):
        assert _pid_is_running(-1) is False
