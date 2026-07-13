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

def _compute_workers() -> int:
    base = _logical_cpus
    if not _enabled:
        return max(1, base // 2)
    # Aggressive scaling for HT + virtual
    multiplier = 4 if _FUSION_PROFILE == "admin" else 2
    if _FUSION_VHT_GPU:
        multiplier = max(multiplier, 6)
    return base * multiplier

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

def enable(enabled: bool = True) -> Dict[str, Any]:
    """Runtime toggle. Used by POST /api/hyperthreading."""
    global _enabled, _workers
    _enabled = bool(enabled)
    _workers = _compute_workers()
    return status()

def disable() -> Dict[str, Any]:
    return enable(False)

def is_hyperthreading_enabled() -> bool:
    return _enabled


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