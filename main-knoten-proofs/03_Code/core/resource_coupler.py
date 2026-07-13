# resource_coupler.py
# CPU + GPU + SSD gekoppelt: autonome Lastverteilung über alle drei Ebenen.

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import psutil

from gpu_memory_allocator import probe_gpu_memory, get_gpu_allocator
from cpu_adaptive_tuner import probe_cpu, get_cpu_tuner
from gpu_compute_booster import get_gpu_compute_booster


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass
class CouplerState:
    running: bool = False
    last_run: float = 0.0
    next_interval_s: float = 4.0
    last_action: str = "idle"
    gpu_target_ratio: float = 0.92
    cpu_performance_ratio: float = 0.67
    llama_gpu_layers: int = 20
    history: list = field(default_factory=list)


class ResourceCoupler:
    """
    Regeln (gekoppelt):
    - RAM > 85 % + VRAM < 70 %  → Workloads auf GPU/SSD verlagern, CPU drosseln
    - VRAM < 50 % + CPU < 40 %  → VRAM-Pool + virtuelle Threads auffüllen
    - CPU heiß (> 75 °C)        → CPU runter, GPU hoch
    - VRAM > 90 %               → SSD-Spill, Pool trimmen
    - RAM + VRAM beide voll     → aggressiver SSD-Spill, Host-Caches leeren
    """

    def __init__(self) -> None:
        self.ram_soft = _env_float("FUSION_RAM_SOFT_PCT", 80.0)
        self.ram_hard = _env_float("FUSION_RAM_HARD_PCT", 90.0)
        self.vram_target = _env_float("FUSION_VRAM_TARGET_RATIO", 0.92)
        self.vram_low = _env_float("FUSION_VRAM_LOW_PCT", 50.0)
        self.compute_low = _env_float("FUSION_GPU_COMPUTE_LOW_PCT", 30.0)
        self.min_interval = _env_float("FUSION_COUPLER_MIN_INTERVAL", 2.0)
        self.max_interval = _env_float("FUSION_COUPLER_MAX_INTERVAL", 15.0)
        self.auto = os.getenv("FUSION_RESOURCE_COUPLER_AUTO", "1").lower() in (
            "1", "true", "yes", "on",
        )
        self.state = CouplerState(gpu_target_ratio=self.vram_target)
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    def _ssd_status(self) -> Dict[str, Any]:
        try:
            from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache
            cache = get_virtual_gpu_ht_cache()
            if cache.ssd_cache and hasattr(cache.ssd_cache, "status"):
                return cache.ssd_cache.status()
        except Exception:
            pass
        base = os.getenv("FUSION_SSD_LONGTERM_CACHE", r"C:\FusionHero\LongTermCache")
        try:
            from pathlib import Path
            p = Path(base)
            files = list(p.glob("*.npy")) if p.exists() else []
            total = sum(f.stat().st_size for f in files)
            return {
                "cached_items": len(files),
                "total_size_mb": round(total / (1024 * 1024), 2),
                "base_dir": str(p),
            }
        except Exception:
            return {"cached_items": 0, "total_size_mb": 0.0, "base_dir": base}

    def _release_host_pressure(self) -> Dict[str, Any]:
        """Host-RAM entlasten: VRAM-Pool freigeben, Host-Thread-States auf SSD."""
        freed_mb = 0.0
        spilled = 0
        alloc = get_gpu_allocator()
        with alloc._lock:
            freed_mb = alloc._release_pool_unsafe()
            if freed_mb > 0:
                alloc.state.last_action = "coupler_released_vram_pool"
        try:
            from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache
            cache = get_virtual_gpu_ht_cache()
            for tid, state in list(cache.vram.items()):
                if cache._is_device_tensor(state):
                    continue
                if cache.ssd_cache:
                    import numpy as np
                    cache.ssd_cache.store(f"vthread_{tid}", np.asarray(state, dtype=np.float32))
                    del cache.vram[tid]
                    spilled += 1
        except Exception:
            pass
        llama_stopped = False
        try:
            from gpu_compute_booster import get_gpu_compute_booster
            llama_stopped = get_gpu_compute_booster().stop_server()
        except Exception:
            pass
        return {
            "freed_vram_pool_mb": freed_mb,
            "spilled_host_threads": spilled,
            "llama_server_stopped": llama_stopped,
        }

    def _boost_gpu(self, snap_gpu, deficit_ratio: float) -> Dict[str, Any]:
        alloc = get_gpu_allocator()
        alloc.target_ratio = min(0.98, self.state.gpu_target_ratio + deficit_ratio * 0.1)
        self.state.gpu_target_ratio = alloc.target_ratio
        os.environ["FUSION_VRAM_TARGET_RATIO"] = str(round(alloc.target_ratio, 3))
        gpu_result = alloc.rebalance_once()
        layers = min(35, max(8, int(snap_gpu.dedicated_total_mb / 120)))
        self.state.llama_gpu_layers = layers
        os.environ["FUSION_LLAMA_GPU_LAYERS"] = str(layers)
        return {"allocator": gpu_result, "llama_gpu_layers": layers}

    def couple_once(self) -> Dict[str, Any]:
        with self._lock:
            gpu_snap = probe_gpu_memory()
            cpu_snap = probe_cpu()
            ssd_snap = self._ssd_status()

            ram_pct = gpu_snap.system_ram_util_pct
            vram_pct = gpu_snap.dedicated_util_pct
            compute_pct = gpu_snap.compute_util_pct
            cpu_load = cpu_snap["load_pct"]
            cpu_temp = cpu_snap.get("temp_c")
            action = "hold"
            details: Dict[str, Any] = {}

            temp_hot = cpu_temp is not None and cpu_temp >= 75.0
            ram_critical = ram_pct >= self.ram_hard
            ram_high = ram_pct >= self.ram_soft
            vram_low = vram_pct < self.vram_low
            vram_high = vram_pct >= 90.0

            if ram_critical or (ram_high and vram_low):
                action = "shift_ram_to_gpu_ssd"
                details["release"] = self._release_host_pressure()
                details["gpu_boost"] = self._boost_gpu(gpu_snap, deficit_ratio=0.15)
                tuner = get_cpu_tuner()
                tuner.state.performance_ratio = max(0.5, tuner.state.performance_ratio - 0.12)
                tuner.state.target_workers = max(
                    cpu_snap["logical_cpus"],
                    tuner.state.target_workers - cpu_snap["logical_cpus"],
                )
                tuner._apply_hyperthreading(
                    tuner.state.performance_ratio, tuner.state.target_workers,
                )
                os.environ["FUSION_OFFLOAD_TO_GPU"] = "1"
                os.environ["FUSION_HOST_RAM_MINIMAL"] = "1"

            elif vram_low and cpu_load < 40.0 and not ram_high:
                action = "fill_gpu_while_cpu_idle"
                details["gpu_boost"] = self._boost_gpu(gpu_snap, deficit_ratio=0.08)
                tuner = get_cpu_tuner()
                if cpu_temp is None or cpu_temp < 72.0:
                    tuner.state.performance_ratio = min(1.0, tuner.state.performance_ratio + 0.05)
                    tuner._apply_hyperthreading(
                        tuner.state.performance_ratio, tuner.state.target_workers,
                    )

            elif temp_hot or cpu_load > 85.0:
                action = "shift_cpu_to_gpu"
                details["gpu_boost"] = self._boost_gpu(gpu_snap, deficit_ratio=0.1)
                tuner = get_cpu_tuner()
                tuner.state.performance_ratio = max(0.5, tuner.state.performance_ratio - 0.1)
                tuner.state.target_workers = max(
                    cpu_snap["logical_cpus"] * 2,
                    tuner.state.target_workers - cpu_snap["logical_cpus"] // 2,
                )
                tuner._apply_hyperthreading(
                    tuner.state.performance_ratio, tuner.state.target_workers,
                )

            elif vram_high and ram_high:
                action = "spill_both_to_ssd"
                details["release"] = self._release_host_pressure()
                alloc = get_gpu_allocator()
                alloc.target_ratio = max(0.75, alloc.target_ratio - 0.05)
                self.state.gpu_target_ratio = alloc.target_ratio
                details["allocator_trim"] = alloc.rebalance_once()

            elif vram_high:
                action = "spill_vram_to_ssd"
                alloc = get_gpu_allocator()
                alloc.target_ratio = max(0.80, alloc.target_ratio - 0.03)
                self.state.gpu_target_ratio = alloc.target_ratio
                details["allocator_trim"] = alloc.rebalance_once()

            elif vram_pct < self.vram_low and ram_pct < 72.0:
                action = "fill_dedicated_vram"
                try:
                    from gpu_vram_prioritizer import get_vram_prioritizer
                    details["vram_prioritizer"] = get_vram_prioritizer().prioritize_once()
                except Exception as exc:
                    details["vram_prioritizer"] = {"error": str(exc)}
            elif compute_pct < self.compute_low and not ram_critical:
                action = "boost_gpu_compute"
                booster = get_gpu_compute_booster()
                details["compute_boost"] = booster.boost_once()
                if vram_pct < 70.0:
                    details["vram_fill"] = self._boost_gpu(gpu_snap, deficit_ratio=0.05)

            self.state.last_action = action
            self.state.last_run = time.time()
            self.state.cpu_performance_ratio = float(
                os.getenv("FUSION_PERFORMANCE_RATIO", "0.67"),
            )

            prev_ram = self.state.history[-1]["ram_pct"] if self.state.history else ram_pct
            delta = abs(ram_pct - prev_ram)
            if delta >= 10:
                self.state.next_interval_s = self.min_interval
            elif delta >= 4:
                self.state.next_interval_s = min(self.max_interval, self.min_interval * 2)
            else:
                self.state.next_interval_s = min(
                    self.max_interval, self.state.next_interval_s * 1.15,
                )

            entry = {
                "ts": self.state.last_run,
                "action": action,
                "ram_pct": ram_pct,
                "vram_pct": vram_pct,
                "compute_pct": compute_pct,
                "cpu_load_pct": cpu_load,
                "cpu_temp_c": cpu_temp,
                "gpu_target_ratio": self.state.gpu_target_ratio,
                "llama_gpu_layers": self.state.llama_gpu_layers,
            }
            self.state.history.append(entry)
            self.state.history = self.state.history[-50:]

            return {
                "status": "ok",
                "action": action,
                "coupling": "cpu_gpu_ssd",
                "memory": gpu_snap.to_dict(),
                "cpu": cpu_snap,
                "ssd": ssd_snap,
                "tuning": entry,
                "details": details,
                "next_interval_s": self.state.next_interval_s,
            }

    def status(self) -> Dict[str, Any]:
        gpu_snap = probe_gpu_memory()
        cpu_snap = probe_cpu()
        with self._lock:
            return {
                "coupler": {
                    "auto_enabled": self.auto,
                    "running": self.state.running,
                    "last_action": self.state.last_action,
                    "gpu_target_ratio": self.state.gpu_target_ratio,
                    "llama_gpu_layers": self.state.llama_gpu_layers,
                    "cpu_performance_ratio": self.state.cpu_performance_ratio,
                    "next_interval_s": round(self.state.next_interval_s, 2),
                    "policy": "ram→gpu→ssd | cpu_hot→gpu | compute_low→boost",
                },
                "memory": gpu_snap.to_dict(),
                "cpu": cpu_snap,
                "ssd": self._ssd_status(),
            }

    def _loop(self) -> None:
        self.state.running = True
        while not self._stop.is_set():
            try:
                self.couple_once()
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
        self._thread = threading.Thread(
            target=self._loop, name="fusion-resource-coupler", daemon=True,
        )
        self._thread.start()
        return True

    def stop_background(self) -> None:
        self._stop.set()


_coupler: Optional[ResourceCoupler] = None


def get_resource_coupler() -> ResourceCoupler:
    global _coupler
    if _coupler is None:
        _coupler = ResourceCoupler()
    return _coupler