"""Tests für globale Prozess-Exklusivität."""

from __future__ import annotations

import os
import sys
import threading
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_CODE = _ROOT / "03_Code"
_DASHBOARD = _CODE / "Dashboard"
for p in (_CODE, _DASHBOARD):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from core import process_exclusivity as pe


def _use_temp_lock_dir(tmp_path: Path, monkeypatch):
    lock_root = tmp_path / "locks"
    monkeypatch.setenv("FUSION_PROCESS_LOCK_DIR", str(lock_root))
    monkeypatch.setenv("FUSION_PROCESS_EXCLUSIVITY", "1")
    monkeypatch.setattr(pe, "_thread_locks", {}, raising=False)
    monkeypatch.setattr(pe, "_held_keys", set(), raising=False)
    pe.lock_dir()


def test_try_acquire_and_release(tmp_path, monkeypatch):
    _use_temp_lock_dir(tmp_path, monkeypatch)
    first = pe.try_acquire("test:resource")
    assert first.ok is True
    second = pe.try_acquire("test:resource")
    assert second.ok is False
    assert second.reason in ("held_by_other_thread", "held_by_other_process")
    assert pe.release("test:resource") is True
    third = pe.try_acquire("test:resource")
    assert third.ok is True
    pe.release("test:resource")


def test_exclusive_context_manager(tmp_path, monkeypatch):
    _use_temp_lock_dir(tmp_path, monkeypatch)
    with pe.exclusive("ctx:key") as lock:
        assert lock.ok is True
        blocked = pe.try_acquire("ctx:key")
        assert blocked.ok is False
    after = pe.try_acquire("ctx:key")
    assert after.ok is True
    pe.release("ctx:key")


def test_disabled_mode_allows_parallel(tmp_path, monkeypatch):
    _use_temp_lock_dir(tmp_path, monkeypatch)
    monkeypatch.setenv("FUSION_PROCESS_EXCLUSIVITY", "0")
    a = pe.try_acquire("free:key")
    b = pe.try_acquire("free:key")
    assert a.ok is True
    assert b.ok is True
    pe.release("free:key")
    pe.release("free:key")


def test_stale_lock_cleanup(tmp_path, monkeypatch):
    _use_temp_lock_dir(tmp_path, monkeypatch)
    path = pe._lock_path("stale:key")
    payload = {
        "key": "stale:key",
        "pid": 999999999,
        "acquired_at": time.time() - 10_000,
        "ttl_sec": 1,
    }
    path.write_text(__import__("json").dumps(payload), encoding="utf-8")
    assert path.exists()
    data = pe._read_lock_file(path)
    assert data is not None
    assert pe._is_stale(data) is True
    removed = pe.cleanup_stale()
    assert removed >= 1
    assert not path.exists()
    result = pe.try_acquire("stale:key")
    assert result.ok is True
    pe.release("stale:key")


def test_thread_parallel_blocks(tmp_path, monkeypatch):
    _use_temp_lock_dir(tmp_path, monkeypatch)
    results: list[bool] = []

    def worker():
        with pe.exclusive("thread:key") as lock:
            results.append(lock.ok)
            time.sleep(0.05)

    t1 = threading.Thread(target=worker)
    t2 = threading.Thread(target=worker)
    t1.start()
    time.sleep(0.01)
    t2.start()
    t1.join()
    t2.join()
    assert results.count(True) == 1
    assert results.count(False) == 1


def test_status_reports_locks(tmp_path, monkeypatch):
    _use_temp_lock_dir(tmp_path, monkeypatch)
    pe.try_acquire("status:key", owner="pytest")
    st = pe.status()
    assert st["enabled"] is True
    assert "status:key" in st["held_in_process"]
    assert st["pid"] == os.getpid()
    pe.release("status:key")