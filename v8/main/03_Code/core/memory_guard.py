# memory_guard.py — RAM-Notfall: Arbeitsspeicher entlasten, GPU/SSD priorisieren

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


def probe_ram() -> Dict[str, Any]:
    mem = psutil.virtual_memory()
    return {
        "total_gb": round(mem.total / (1024 ** 3), 2),
        "used_gb": round(mem.used / (1024 ** 3), 2),
        "available_gb": round(mem.available / (1024 ** 3), 2),
        "util_pct": mem.percent,
    }


@dataclass
class GuardState:
    running: bool = False
    last_action: str = "idle"
    last_run: float = 0.0
    next_interval_s: float = 5.0
    history: list = field(default_factory=list)


class MemoryGuard:
    def __init__(self) -> None:
        self.soft = _env_float("FUSION_RAM_SOFT_PCT", 80.0)
        self.hard = _env_float("FUSION_RAM_HARD_PCT", 88.0)
        self.critical = _env_float("FUSION_RAM_CRITICAL_PCT", 92.0)
        self.auto = os.getenv("FUSION_MEMORY_GUARD_AUTO", "1").lower() in ("1", "true", "yes", "on")
        self.state = GuardState()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    def _stop_llama_server(self) -> bool:
        stopped = False
        try:
            from gpu_compute_booster import get_gpu_compute_booster
            if get_gpu_compute_booster().stop_server():
                stopped = True
        except Exception:
            pass
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info["name"] and "llama-server" in proc.info["name"].lower():
                    proc.terminate()
                    stopped = True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return stopped

    def _release_pools(self) -> Dict[str, Any]:
        freed = 0.0
        spilled = 0
        try:
            from gpu_memory_allocator import get_gpu_allocator
            freed = get_gpu_allocator().release_pool()
        except Exception:
            pass
        try:
            from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache
            import numpy as np
            cache = get_virtual_gpu_ht_cache()
            for tid, state in list(cache.vram.items()):
                if cache._is_device_tensor(state):
                    continue
                if cache.ssd_cache:
                    cache.ssd_cache.store(f"vthread_{tid}", np.asarray(state, dtype=np.float32))
                    del cache.vram[tid]
                    spilled += 1
        except Exception:
            pass
        return {"freed_vram_pool_mb": freed, "spilled_host_threads": spilled}

    def relieve_once(self) -> Dict[str, Any]:
        with self._lock:
            ram = probe_ram()
            pct = ram["util_pct"]
            action = "hold"
            details: Dict[str, Any] = {}

            try:
                from gpu_memory_allocator import probe_gpu_memory
                vram_pct = probe_gpu_memory().dedicated_util_pct
            except Exception:
                vram_pct = 100.0
            vram_underfilled = vram_pct < float(os.getenv("FUSION_VRAM_FILL_BELOW_PCT", "45"))

            if pct >= self.critical:
                action = "critical_ram_release"
                details["llama_stopped"] = self._stop_llama_server()
                details["release"] = self._release_pools()
                os.environ["FUSION_GPU_COMPUTE_BOOSTER_AUTO"] = "0"
                os.environ["FUSION_HOST_RAM_MINIMAL"] = "1"
                try:
                    from cpu_adaptive_tuner import get_cpu_tuner
                    tuner = get_cpu_tuner()
                    tuner.state.performance_ratio = 0.5
                    tuner.state.target_workers = psutil.cpu_count(logical=True) or 6
                    tuner._apply_hyperthreading(0.5, tuner.state.target_workers)
                except Exception:
                    pass
            elif pct >= self.hard and not (vram_underfilled and pct < self.critical):
                action = "hard_ram_release"
                details["llama_stopped"] = self._stop_llama_server()
                details["release"] = self._release_pools()
                os.environ["FUSION_GPU_COMPUTE_BOOSTER_AUTO"] = "0"
            elif pct >= self.hard and vram_underfilled:
                action = "hard_ram_keep_gpu"
                details["release"] = self._release_pools()
                details["note"] = "llama-server behalten — VRAM unter Ziel"
            elif pct >= self.soft:
                action = "soft_ram_trim"
                details["release"] = self._release_pools()
            elif pct < self.soft - 10:
                os.environ.setdefault("FUSION_GPU_COMPUTE_BOOSTER_AUTO", "1")

            self.state.last_action = action
            self.state.last_run = time.time()
            if pct >= self.hard:
                self.state.next_interval_s = 3.0
            elif pct >= self.soft:
                self.state.next_interval_s = 5.0
            else:
                self.state.next_interval_s = 15.0

            return {
                "status": "ok",
                "action": action,
                "ram": ram,
                "details": details,
                "next_interval_s": self.state.next_interval_s,
            }

    def status(self) -> Dict[str, Any]:
        return {
            "guard": {
                "auto_enabled": self.auto,
                "running": self.state.running,
                "last_action": self.state.last_action,
                "thresholds": {"soft": self.soft, "hard": self.hard, "critical": self.critical},
            },
            "ram": probe_ram(),
        }

    def _loop(self) -> None:
        self.state.running = True
        while not self._stop.is_set():
            try:
                self.relieve_once()
            except Exception as exc:
                self.state.last_action = f"error:{exc}"
            self._stop.wait(self.state.next_interval_s)
        self.state.running = False

    def start_background(self) -> bool:
        if self._thread and self._thread.is_alive():
            return False
        if not self.auto:
            return False
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="fusion-memory-guard", daemon=True)
        self._thread.start()
        return True


_guard: Optional[MemoryGuard] = None


def get_memory_guard() -> MemoryGuard:
    global _guard
    if _guard is None:
        _guard = MemoryGuard()
    return _guard