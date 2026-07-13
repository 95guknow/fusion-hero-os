# hyperthreading_config.py
# Fusion Hero OS - Hyperthreading Configuration & Runtime Control
# Supports FUSION_HYPERTHREADING=1 + virtual GPU HT
#
# Provides:
#   status() -> dict
#   enable(bool)
#   parallel_workers() -> int
#   get_virtual_workers() etc.

import os
import multiprocessing
from typing import Dict, Any

# --- Defaults from env (set in run_backend.bat / start_all / activate scripts) ---
_FUSION_HT = os.getenv("FUSION_HYPERTHREADING", "1").lower() in ("1", "true", "yes", "on")
_FUSION_PROFILE = os.getenv("FUSION_PROFILE", "admin").lower()
_FUSION_RATIO = float(os.getenv("FUSION_PERFORMANCE_RATIO", "1.0"))
_FUSION_VHT_GPU = os.getenv("FUSION_VIRTUAL_HT_GPU", "1").lower() in ("1", "true", "yes", "on")
_FUSION_VTHREADS = int(os.getenv("FUSION_VIRTUAL_THREADS", "64"))
_FUSION_VSTATE = int(os.getenv("FUSION_VIRTUAL_STATE_SIZE", "256"))
_FUSION_GPU_STREAMS = int(os.getenv("FUSION_GPU_STREAMS", "8"))

# Runtime state (can be toggled via API)
_enabled: bool = _FUSION_HT
_logical_cpus: int = os.cpu_count() or multiprocessing.cpu_count() or 12

# Spectrum support (0.0 = no HT, 1.0 = standard HT, 1.5-2.0 = aggressive virtual/oversub)
# Self-regulating: autorgenerativ via metrics (load, cache, power, task_type)
_HT_SPECTRUM: float = float(os.getenv("FUSION_HT_SPECTRUM", "1.0"))
_HT_ADAPTIVE: bool = os.getenv("FUSION_HT_ADAPTIVE", "1").lower() in ("1", "true", "yes", "on")

def _compute_workers() -> int:
    base = _logical_cpus
    if not _enabled:
        return max(1, base // 2)
    # Spectrum-based: scale workers by spectrum value
    spectrum = max(0.0, min(2.0, _HT_SPECTRUM))
    multiplier = 2.0 + (spectrum * 2.0)  # 2.0 at 0.0 → 6.0 at 2.0
    if _FUSION_VHT_GPU:
        multiplier = max(multiplier, 4.0 + (spectrum * 2.0))
    if _FUSION_PROFILE == "admin":
        multiplier *= 1.2
    workers = int(base * multiplier)
    return max(1, workers)

_workers: int = _compute_workers()

def status() -> Dict[str, Any]:
    """Current hyperthreading status (used by health, UI, scripts)."""
    base = {
        "enabled": _enabled,
        "logical_cpus": _logical_cpus,
        "workers": _workers,
        "performance_ratio": _FUSION_RATIO,
        "profile": _FUSION_PROFILE,
        "virtual_ht_gpu": _FUSION_VHT_GPU,
        "virtual_threads": _FUSION_VTHREADS if _FUSION_VHT_GPU else 0,
        "gpu_streams": _FUSION_GPU_STREAMS if _FUSION_VHT_GPU else 0,
        "fusion_hyperthreading_env": _FUSION_HT,
        "ht_spectrum": _HT_SPECTRUM,
        "ht_adaptive": _HT_ADAPTIVE,
    }
    if _FUSION_VHT_GPU:
        try:
            cache = get_virtual_gpu_ht_cache()
            if hasattr(cache, "status"):
                vstatus = cache.status()
                base.update({
                    "virtual_cache_status": vstatus,
                    "virtual_threads_active": vstatus.get("active_virtual_threads", 0),
                })
        except:
            pass
    try:
        from gpu_memory_allocator import get_gpu_allocator
        alloc = get_gpu_allocator().status().get("allocator", {})
        base["gpu_allocator"] = alloc
    except Exception:
        pass
    return base

def set_ht_spectrum(spectrum: float) -> Dict[str, Any]:
    """Set spectrum (0.0-2.0). Used for spectrum-based control instead of binary."""
    global _HT_SPECTRUM, _workers
    _HT_SPECTRUM = max(0.0, min(2.0, float(spectrum)))
    _workers = _compute_workers()
    return status()

def self_regulate_ht(metrics: Dict[str, float] = None) -> Dict[str, Any]:
    """Autorgenerativ selbstregelnd: adjust spectrum based on runtime metrics.
    Instead of on/off. Call periodically from resource_workflow or optimizer.
    """
    global _HT_SPECTRUM, _workers
    if not _HT_ADAPTIVE:
        return status()
    m = metrics or {}
    load = m.get("cpu_load", 0.5)
    cache_miss = m.get("cache_miss_rate", 0.1)
    power = m.get("power_factor", 1.0)
    task_type = m.get("task_type_factor", 1.0)  # e.g. 1.2 for llm heavy

    # Spectrum formula: base + adjustments, self-regulating
    adjustment = (0.3 * (1.0 - load)) + (0.2 * (1.0 - cache_miss)) - (0.1 * (power - 1.0)) + (0.1 * (task_type - 1.0))
    new_spectrum = max(0.0, min(2.0, _HT_SPECTRUM + adjustment * 0.1))
    if abs(new_spectrum - _HT_SPECTRUM) > 0.05:
        _HT_SPECTRUM = new_spectrum
        _workers = _compute_workers()
    return status()

def enable(enabled: bool = True) -> Dict[str, Any]:
    """Runtime toggle. Legacy binary path (maps to spectrum 0/1)."""
    global _enabled, _HT_SPECTRUM, _workers
    _enabled = bool(enabled)
    _HT_SPECTRUM = 1.0 if _enabled else 0.0
    _workers = _compute_workers()
    return status()

def disable() -> Dict[str, Any]:
    return enable(False)

def is_hyperthreading_enabled() -> bool:
    return _enabled and _HT_SPECTRUM > 0.1


def logical_cpu_count() -> int:
    return _logical_cpus


def parallel_workers(override: int | None = None) -> int:
    """Number of parallel workers / HT tracks to use."""
    if override is not None and override > 0:
        return override
    return _workers

def get_virtual_gpu_ht_cache():
    """Returns the real Virtual GPU HT cache (with SSD spill if configured).
    Falls back to dict if virtual HT disabled.
    """
    if not _FUSION_VHT_GPU:
        return {"enabled": False}
    try:
        from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache as _real_get
        cache = _real_get()
        # Also init SSD if not present
        try:
            from ssd_longterm_cache import SSDLongTermCache
            # attach if needed
        except:
            pass
        return cache
    except Exception as e:
        print(f"[hyperthreading_config] virtual_gpu_hyperthreading import failed: {e}")
        return {
            "enabled": True,
            "virtual_threads": _FUSION_VTHREADS,
            "state_size": _FUSION_VSTATE,
            "gpu_streams": _FUSION_GPU_STREAMS,
            "share_factor": float(os.getenv("FUSION_GPU_SHARE_FACTOR", "3.0")),
            "note": "simulated (real module not loadable)"
        }

# Auto-activate on import if env requests it (consistent with "immer automatisch")
if _FUSION_HT:
    enable(True)

if __name__ == "__main__":
    import json
    print(json.dumps(status(), indent=2))
    print("Effective workers:", parallel_workers())