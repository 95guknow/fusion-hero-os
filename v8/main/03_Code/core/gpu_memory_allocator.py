# gpu_memory_allocator.py
# Adaptive VRAM-Steuerung: dedizierter Grafikspeicher priorisieren,
# System-RAM für GPU-Workloads minimal halten.

from __future__ import annotations

import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import psutil


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass
class GPUMemorySnapshot:
    name: str = "unknown"
    dedicated_total_mb: float = 0.0
    dedicated_free_mb: float = 0.0
    dedicated_used_mb: float = 0.0
    dedicated_util_pct: float = 0.0
    compute_util_pct: float = 0.0
    system_ram_total_mb: float = 0.0
    system_ram_used_mb: float = 0.0
    system_ram_free_mb: float = 0.0
    system_ram_util_pct: float = 0.0
    cuda_available: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gpu_name": self.name,
            "dedicated_vram": {
                "total_mb": round(self.dedicated_total_mb, 1),
                "used_mb": round(self.dedicated_used_mb, 1),
                "free_mb": round(self.dedicated_free_mb, 1),
                "util_pct": round(self.dedicated_util_pct, 1),
            },
            "compute": {
                "util_pct": round(self.compute_util_pct, 1),
            },
            "system_ram": {
                "total_mb": round(self.system_ram_total_mb, 1),
                "used_mb": round(self.system_ram_used_mb, 1),
                "free_mb": round(self.system_ram_free_mb, 1),
                "util_pct": round(self.system_ram_util_pct, 1),
            },
            "cuda_available": self.cuda_available,
        }


def probe_gpu_memory() -> GPUMemorySnapshot:
    snap = GPUMemorySnapshot()
    mem = psutil.virtual_memory()
    snap.system_ram_total_mb = mem.total / (1024 ** 2)
    snap.system_ram_used_mb = mem.used / (1024 ** 2)
    snap.system_ram_free_mb = mem.available / (1024 ** 2)
    snap.system_ram_util_pct = mem.percent

    try:
        result = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,memory.free,memory.used,utilization.gpu",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True,
            text=True,
            timeout=8,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = [p.strip() for p in result.stdout.strip().split(",")]
            if len(parts) >= 4:
                snap.name = parts[0]
                snap.dedicated_total_mb = float(parts[1])
                snap.dedicated_free_mb = float(parts[2])
                snap.dedicated_used_mb = float(parts[3])
                if snap.dedicated_total_mb > 0:
                    snap.dedicated_util_pct = (
                        snap.dedicated_used_mb / snap.dedicated_total_mb
                    ) * 100.0
                if len(parts) >= 5 and parts[4]:
                    try:
                        snap.compute_util_pct = float(parts[4])
                    except ValueError:
                        pass
                snap.cuda_available = True
                return snap
    except Exception:
        pass

    try:
        import cupy as cp
        if cp.cuda.is_available():
            free_b, total_b = cp.cuda.Device(0).mem_info
            snap.cuda_available = True
            snap.dedicated_total_mb = total_b / (1024 ** 2)
            snap.dedicated_free_mb = free_b / (1024 ** 2)
            snap.dedicated_used_mb = snap.dedicated_total_mb - snap.dedicated_free_mb
            if snap.dedicated_total_mb > 0:
                snap.dedicated_util_pct = (
                    snap.dedicated_used_mb / snap.dedicated_total_mb
                ) * 100.0
    except Exception:
        pass

    return snap


@dataclass
class AllocatorState:
    running: bool = False
    last_run: float = 0.0
    next_interval_s: float = 5.0
    target_vram_ratio: float = 0.92
    last_action: str = "idle"
    history: list = field(default_factory=list)


class AdaptiveGPUAllocator:
    """Füllt dedizierten VRAM adaptiv; hält Host-RAM für GPU-Caches leer."""

    def __init__(self) -> None:
        self.target_ratio = _env_float("FUSION_VRAM_TARGET_RATIO", 0.92)
        self.min_interval = _env_float("FUSION_GPU_ALLOCATOR_MIN_INTERVAL", 2.0)
        self.max_interval = _env_float("FUSION_GPU_ALLOCATOR_MAX_INTERVAL", 30.0)
        self.auto_enabled = os.getenv("FUSION_GPU_ALLOCATOR_AUTO", "1").lower() in (
            "1", "true", "yes", "on",
        )
        self.state = AllocatorState(target_vram_ratio=self.target_ratio)
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._vram_pool_mb = 0.0
        self._pool_tensors: list = []

    def status(self) -> Dict[str, Any]:
        snap = probe_gpu_memory()
        with self._lock:
            return {
                "allocator": {
                    "auto_enabled": self.auto_enabled,
                    "running": self.state.running,
                    "target_vram_ratio": self.target_ratio,
                    "next_interval_s": round(self.state.next_interval_s, 2),
                    "last_action": self.state.last_action,
                    "vram_pool_mb": round(self._vram_pool_mb, 1),
                    "last_run": self.state.last_run,
                },
                "memory": snap.to_dict(),
                "policy": "dedicated_vram_first | system_ram_minimal | ssd_spill",
            }

    def _adaptive_interval(self, snap: GPUMemorySnapshot, prev_util: Optional[float]) -> float:
        if prev_util is None:
            return self.min_interval
        delta = abs(snap.dedicated_util_pct - prev_util)
        if delta >= 8.0:
            return self.min_interval
        if delta >= 3.0:
            return min(self.max_interval, self.min_interval * 3)
        return min(self.max_interval, self.state.next_interval_s * 1.25)

    def _release_pool_unsafe(self) -> float:
        freed = self._vram_pool_mb
        self._pool_tensors.clear()
        self._vram_pool_mb = 0.0
        if freed > 0:
            self.state.last_action = "released_vram_pool"
        return freed

    def release_pool(self) -> float:
        """VRAM-Pool freigeben (RAM-Druck / Coupler-Anforderung)."""
        with self._lock:
            return self._release_pool_unsafe()

    def _resize_vram_pool(self, snap: GPUMemorySnapshot) -> float:
        """Pre-allocate GPU buffers to approach target VRAM utilization."""
        if not snap.cuda_available or snap.dedicated_total_mb <= 0:
            return 0.0
        if snap.system_ram_util_pct >= _env_float("FUSION_RAM_SOFT_PCT", 80.0):
            self.state.last_action = "vram_pool_skipped_ram_pressure"
            return 0.0

        target_used_mb = snap.dedicated_total_mb * self.target_ratio
        deficit_mb = max(0.0, target_used_mb - snap.dedicated_used_mb - self._vram_pool_mb)
        if deficit_mb < 32.0:
            self.state.last_action = "vram_near_target"
            return 0.0

        chunk_mb = min(deficit_mb, 256.0)
        elems = int((chunk_mb * 1024 * 1024) / 4)
        if elems < 1024:
            return 0.0

        allocated = 0.0
        try:
            import torch
            if torch.cuda.is_available():
                t = torch.empty(elems, dtype=torch.float32, device="cuda")
                self._pool_tensors.append(t)
                allocated = chunk_mb
                self._vram_pool_mb += chunk_mb
                self.state.last_action = f"allocated_vram_pool_{chunk_mb:.0f}mb"
                return allocated
        except Exception:
            pass

        try:
            import cupy as cp
            if cp.cuda.is_available():
                t = cp.empty(elems, dtype=cp.float32)
                self._pool_tensors.append(t)
                allocated = chunk_mb
                self._vram_pool_mb += chunk_mb
                self.state.last_action = f"allocated_vram_pool_cupy_{chunk_mb:.0f}mb"
                return allocated
        except Exception:
            pass

        self.state.last_action = "vram_pool_alloc_failed"
        return allocated

    def _rebalance_virtual_cache(self, snap: GPUMemorySnapshot) -> Dict[str, Any]:
        try:
            from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache
            cache = get_virtual_gpu_ht_cache()
            if hasattr(cache, "rebalance_to_dedicated_vram"):
                return cache.rebalance_to_dedicated_vram(
                    target_ratio=self.target_ratio,
                    snap=snap.to_dict(),
                )
            if snap.cuda_available and hasattr(cache, "allocate_virtual_thread"):
                added = 0
                target_threads = int(
                    (snap.dedicated_total_mb * self.target_ratio * 1024 * 1024)
                    / max(getattr(cache, "state_size", 256) * 4, 1)
                )
                target_threads = min(target_threads, 8192)
                while len(cache.vram) < target_threads and len(cache.vram) < cache.max_threads:
                    tid = cache.allocate_virtual_thread()
                    if tid is None:
                        break
                    added += 1
                if added:
                    cache.max_threads = max(cache.max_threads, len(cache.vram) + 64)
                    self.state.last_action = f"virtual_threads_{added}_on_vram"
                return {"virtual_threads_added": added, "active": len(cache.vram)}
        except Exception as exc:
            return {"error": str(exc)}
        return {"skipped": True}

    def rebalance_once(self) -> Dict[str, Any]:
        with self._lock:
            snap = probe_gpu_memory()
            prev_util = None
            if self.state.history:
                prev_util = self.state.history[-1].get("dedicated_util_pct")

            if snap.system_ram_util_pct >= _env_float("FUSION_RAM_HARD_PCT", 90.0):
                self._release_pool_unsafe()

            pool_mb = self._resize_vram_pool(snap)
            vcache = self._rebalance_virtual_cache(snap)
            snap_after = probe_gpu_memory()

            self.state.last_run = time.time()
            self.state.next_interval_s = self._adaptive_interval(snap_after, prev_util)
            entry = {
                "ts": self.state.last_run,
                "dedicated_util_pct": snap_after.dedicated_util_pct,
                "system_ram_util_pct": snap_after.system_ram_util_pct,
                "action": self.state.last_action,
                "pool_added_mb": pool_mb,
            }
            self.state.history.append(entry)
            self.state.history = self.state.history[-50:]

            return {
                "status": "ok",
                "before": snap.to_dict(),
                "after": snap_after.to_dict(),
                "action": self.state.last_action,
                "pool_added_mb": pool_mb,
                "virtual_cache": vcache,
                "next_interval_s": self.state.next_interval_s,
            }

    def _loop(self) -> None:
        self.state.running = True
        while not self._stop.is_set():
            try:
                self.rebalance_once()
            except Exception as exc:
                self.state.last_action = f"error:{exc}"
            self._stop.wait(self.state.next_interval_s)
        self.state.running = False

    def start_background(self) -> bool:
        if self._thread and self._thread.is_alive():
            return False
        if not self.auto_enabled:
            return False
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop,
            name="fusion-gpu-allocator",
            daemon=True,
        )
        self._thread.start()
        return True

    def stop_background(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)


_allocator: Optional[AdaptiveGPUAllocator] = None


def get_gpu_allocator() -> AdaptiveGPUAllocator:
    global _allocator
    if _allocator is None:
        _allocator = AdaptiveGPUAllocator()
    return _allocator