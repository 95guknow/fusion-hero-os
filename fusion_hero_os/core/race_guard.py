"""
RaceConditionGuard — concurrent-safe file IO for Fusion Hero OS mesh/coord paths.

Protects multi-writer scenarios (desktop + GCE cron + optional cluster jobs):
  * exclusive file locks (Windows msvcrt / POSIX fcntl)
  * atomic write: temp file + fsync + os.replace
  * compare-and-swap JSON with generation counter
  * optional concurrent stress harness for CI

Platform: Windows + Linux (GCE fusion-mesh-exit).
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import threading
import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union
from collections.abc import Callable, Iterator

PathLike = Union[str, Path]

__all__ = [
    "RaceConditionGuard",
    "FileLock",
    "atomic_write_text",
    "atomic_write_json",
    "locked_atomic_write_json",
    "compare_and_swap_json",
    "race_stress_test",
]


def _as_path(p: PathLike) -> Path:
    return p if isinstance(p, Path) else Path(p)


# ---------------------------------------------------------------------------
# File lock (cross-platform)
# ---------------------------------------------------------------------------


class FileLock:
    """Exclusive advisory lock on a companion ``.lock`` file.

    Raises ``TimeoutError`` if the lock cannot be acquired within ``timeout``.
    """

    def __init__(self, target: PathLike, timeout: float = 30.0, poll: float = 0.05):
        self.target = _as_path(target)
        self.lock_path = self.target.with_suffix(self.target.suffix + ".lock")
        self.timeout = timeout
        self.poll = poll
        self._fh = None  # type: ignore[var-annotated]

    def acquire(self) -> None:
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        deadline = time.monotonic() + self.timeout
        while True:
            fh = open(self.lock_path, "a+b")
            try:
                if sys.platform == "win32":
                    import msvcrt

                    # lock 1 byte from start
                    fh.seek(0)
                    if fh.read(1) == b"":
                        fh.write(b"\0")
                        fh.flush()
                    fh.seek(0)
                    msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                self._fh = fh
                return
            except (OSError, BlockingIOError):
                fh.close()
                if time.monotonic() >= deadline:
                    raise TimeoutError(
                        f"FileLock timeout after {self.timeout}s: {self.lock_path}"
                    )
                time.sleep(self.poll)

    def release(self) -> None:
        if self._fh is None:
            return
        try:
            if sys.platform == "win32":
                import msvcrt

                self._fh.seek(0)
                try:
                    msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
                except OSError:
                    pass
            else:
                import fcntl

                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        finally:
            try:
                self._fh.close()
            except OSError:
                pass
            self._fh = None

    def __enter__(self) -> FileLock:
        self.acquire()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.release()


@contextmanager
def file_lock(target: PathLike, timeout: float = 30.0) -> Iterator[FileLock]:
    lock = FileLock(target, timeout=timeout)
    lock.acquire()
    try:
        yield lock
    finally:
        lock.release()


# ---------------------------------------------------------------------------
# Atomic writes
# ---------------------------------------------------------------------------


def atomic_write_text(
    path: PathLike,
    data: str,
    *,
    encoding: str = "utf-8",
    make_parents: bool = True,
) -> Path:
    """Write ``data`` atomically: temp in same dir → fsync → os.replace."""
    path = _as_path(path)
    if make_parents:
        path.parent.mkdir(parents=True, exist_ok=True)
    # Same filesystem for replace
    fd, tmp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=f".{uuid.uuid4().hex[:8]}.tmp",
        dir=str(path.parent),
    )
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding=encoding, newline="\n") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(str(tmp_path), str(path))
        # best-effort dir fsync (POSIX)
        if sys.platform != "win32":
            try:
                dir_fd = os.open(str(path.parent), os.O_RDONLY)
                try:
                    os.fsync(dir_fd)
                finally:
                    os.close(dir_fd)
            except OSError:
                pass
    except Exception:
        try:
            tmp_path.unlink(missing_ok=True)  # type: ignore[call-arg]
        except TypeError:
            if tmp_path.exists():
                tmp_path.unlink()
        raise
    return path


def atomic_write_json(
    path: PathLike,
    obj: Any,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
) -> Path:
    text = json.dumps(obj, indent=indent, ensure_ascii=ensure_ascii)
    if not text.endswith("\n"):
        text += "\n"
    return atomic_write_text(path, text)


def locked_atomic_write_json(
    path: PathLike,
    obj: Any,
    *,
    timeout: float = 30.0,
    indent: int = 2,
) -> Path:
    """Exclusive lock + atomic JSON write (safe under multi-process writers)."""
    path = _as_path(path)
    with FileLock(path, timeout=timeout):
        return atomic_write_json(path, obj, indent=indent)


# ---------------------------------------------------------------------------
# Compare-and-swap JSON (generation counter)
# ---------------------------------------------------------------------------


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def compare_and_swap_json(
    path: PathLike,
    mutate: Callable[[dict[str, Any] | None], dict[str, Any]],
    *,
    timeout: float = 30.0,
    max_retries: int = 8,
    expected_generation: int | None = None,
) -> dict[str, Any]:
    """Lock, read, mutate, write with ``_generation`` bump.

    If ``expected_generation`` is set and file generation differs, raises
    ``RuntimeError`` (optimistic concurrency failure after lock).

    Returns the written object.
    """
    path = _as_path(path)
    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            with FileLock(path, timeout=timeout):
                current = _read_json(path)
                gen = 0
                if isinstance(current, dict):
                    gen = int(current.get("_generation") or 0)
                if expected_generation is not None and gen != expected_generation:
                    raise RuntimeError(
                        f"CAS generation mismatch: file={gen} expected={expected_generation}"
                    )
                new_obj = mutate(current)
                if not isinstance(new_obj, dict):
                    raise TypeError("mutate() must return a dict")
                new_obj = dict(new_obj)
                new_obj["_generation"] = gen + 1
                new_obj["_updated_at"] = time.time()
                new_obj["_writer"] = {
                    "pid": os.getpid(),
                    "host": os.environ.get("COMPUTERNAME")
                    or os.environ.get("HOSTNAME")
                    or "unknown",
                }
                atomic_write_json(path, new_obj)
                return new_obj
        except TimeoutError as exc:
            last_err = exc
            time.sleep(0.05 * (attempt + 1))
    raise TimeoutError(f"compare_and_swap_json failed after {max_retries} tries: {last_err}")


# ---------------------------------------------------------------------------
# High-level guard + stress test
# ---------------------------------------------------------------------------


@dataclass
class RaceConditionGuard:
    """Facade used by mesh coordinator / file share / fractal mesh."""

    default_timeout: float = 30.0
    stats: dict[str, int] = field(default_factory=lambda: {
        "writes": 0,
        "locks": 0,
        "cas": 0,
        "timeouts": 0,
    })
    _thread_lock: threading.Lock = field(default_factory=threading.Lock)

    def write_json(self, path: PathLike, obj: Any) -> Path:
        with self._thread_lock:
            self.stats["locks"] += 1
        try:
            p = locked_atomic_write_json(path, obj, timeout=self.default_timeout)
            with self._thread_lock:
                self.stats["writes"] += 1
            return p
        except TimeoutError:
            with self._thread_lock:
                self.stats["timeouts"] += 1
            raise

    def write_text(self, path: PathLike, data: str) -> Path:
        path = _as_path(path)
        with FileLock(path, timeout=self.default_timeout):
            with self._thread_lock:
                self.stats["locks"] += 1
            p = atomic_write_text(path, data)
            with self._thread_lock:
                self.stats["writes"] += 1
            return p

    def cas(
        self,
        path: PathLike,
        mutate: Callable[[dict[str, Any] | None], dict[str, Any]],
        **kwargs: Any,
    ) -> dict[str, Any]:
        with self._thread_lock:
            self.stats["cas"] += 1
        return compare_and_swap_json(path, mutate, timeout=self.default_timeout, **kwargs)


def race_stress_test(
    path: PathLike,
    *,
    n_workers: int = 8,
    n_writes_each: int = 20,
) -> dict[str, Any]:
    """Concurrent writers; verifies final ``_generation`` == total writes and JSON intact."""
    path = _as_path(path)
    if path.exists():
        path.unlink()
    lock_side = path.with_suffix(path.suffix + ".lock")
    if lock_side.exists():
        try:
            lock_side.unlink()
        except OSError:
            pass

    errors: list = []
    barrier = threading.Barrier(n_workers)

    def worker(wid: int) -> None:
        try:
            barrier.wait(timeout=10)
            for i in range(n_writes_each):
                def mut(cur: dict[str, Any] | None, _w=wid, _i=i) -> dict[str, Any]:
                    base = dict(cur or {})
                    hist = list(base.get("history") or [])
                    hist.append(f"w{_w}-{_i}")
                    # keep history bounded
                    base["history"] = hist[-200:]
                    base["last_worker"] = _w
                    return base

                compare_and_swap_json(path, mut, timeout=60.0, max_retries=32)
        except Exception as exc:  # noqa: BLE001
            errors.append(f"worker{wid}: {exc}")

    threads = [threading.Thread(target=worker, args=(w,)) for w in range(n_workers)]
    t0 = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=120)
    elapsed = time.perf_counter() - t0

    final = _read_json(path) or {}
    expected_gen = n_workers * n_writes_each
    gen = int(final.get("_generation") or 0)
    ok = gen == expected_gen and not errors
    return {
        "ok": ok,
        "expected_generation": expected_gen,
        "actual_generation": gen,
        "errors": errors[:10],
        "elapsed_sec": round(elapsed, 4),
        "path": str(path),
        "history_len": len(final.get("history") or []),
    }


# module-level singleton for simple imports
default_guard = RaceConditionGuard()
