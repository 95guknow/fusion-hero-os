# gpu_vram_prioritizer.py — dedizierten VRAM füllen, System-RAM schonen

from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

from gpu_memory_allocator import probe_gpu_memory


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


class GPUVramPrioritizer:
    """Startet llama-server (GPU-Offload) wenn VRAM unter Ziel und RAM frei genug."""

    def __init__(self) -> None:
        self.vram_target_pct = _env_float("FUSION_VRAM_TARGET_PCT", 0.85) * 100.0
        self.vram_low_pct = _env_float("FUSION_VRAM_FILL_BELOW_PCT", 45.0)
        self.ram_max_pct = _env_float("FUSION_VRAM_FILL_RAM_MAX_PCT", 72.0)
        self.ctx_size = _env_int("FUSION_LLAMA_CTX_SIZE", 2048)
        self.gpu_layers = _env_int("FUSION_LLAMA_GPU_LAYERS", 99)

    def prioritize_once(self) -> Dict[str, Any]:
        snap = probe_gpu_memory()
        vram_pct = snap.dedicated_util_pct
        ram_pct = snap.system_ram_util_pct
        action = "hold"
        details: Dict[str, Any] = {}

        vram_target = self.vram_target_pct
        if vram_pct < self.vram_low_pct and ram_pct < self.ram_max_pct:
            action = "fill_vram_llama_server"
            os.environ["FUSION_LLAMA_GPU_LAYERS"] = str(self.gpu_layers)
            os.environ["FUSION_LLAMA_CTX_SIZE"] = str(self.ctx_size)
            os.environ["FUSION_OFFLOAD_TO_GPU"] = "1"
            os.environ["FUSION_HOST_RAM_MINIMAL"] = "1"
            try:
                from gpu_compute_booster import get_gpu_compute_booster
                booster = get_gpu_compute_booster()
                booster._gpu_layers = self.gpu_layers
                booster._ctx_size = self.ctx_size
                booster._ram_soft = self.ram_max_pct + 5
                if booster._ensure_llama_server():
                    burst = booster._run_llama_server_burst(tokens=16)
                    details["llama_server"] = burst
                    details["server_started"] = True
                else:
                    details["server_started"] = False
            except Exception as exc:
                details["error"] = str(exc)

            try:
                from gpu_memory_allocator import get_gpu_allocator
                alloc = get_gpu_allocator()
                alloc.target_ratio = _env_float("FUSION_VRAM_TARGET_RATIO", 0.85)
                details["allocator"] = alloc.rebalance_once()
            except Exception:
                pass

        elif vram_pct >= vram_target - 5:
            action = "vram_at_target"

        snap_after = probe_gpu_memory()
        return {
            "status": "ok",
            "action": action,
            "before": {
                "vram_pct": vram_pct,
                "ram_pct": ram_pct,
                "vram_used_mb": snap.dedicated_used_mb,
                "vram_total_mb": snap.dedicated_total_mb,
            },
            "after": {
                "vram_pct": snap_after.dedicated_util_pct,
                "ram_pct": snap_after.system_ram_util_pct,
                "vram_used_mb": snap_after.dedicated_used_mb,
                "compute_pct": snap_after.compute_util_pct,
            },
            "target_vram_pct": vram_target,
            "details": details,
        }


_prioritizer: Optional[GPUVramPrioritizer] = None


def get_vram_prioritizer() -> GPUVramPrioritizer:
    global _prioritizer
    if _prioritizer is None:
        _prioritizer = GPUVramPrioritizer()
    return _prioritizer