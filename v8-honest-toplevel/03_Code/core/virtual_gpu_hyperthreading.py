# virtual_gpu_hyperthreading.py
# Virtual Hyper-Threading over GPU VRAM Caches + SSD spill-over
# For FUSION_HERO_OS - enables thousands of virtual threads by caching states in GPU VRAM
# Falls back to system RAM / SSD if no GPU

import os
import time
import numpy as np
from pathlib import Path

class VirtualGPUHTCache:
    """Simulates hyper-parallel threads with states cached in 'VRAM' (GPU mem or host mem).
    Used for massive parallel QUBO, annealing, agent workers etc.
    """

    def __init__(self):
        self.state_size = int(os.getenv("FUSION_VIRTUAL_STATE_SIZE", "256"))
        self.max_threads = int(os.getenv("FUSION_VIRTUAL_THREADS", "64"))
        self.use_gpu = os.getenv("FUSION_USE_GPU", "1") == "1" and self._has_gpu()
        self.vram = {}  # tid -> np.array state
        self.next_tid = 0
        self.ssd_cache = SSDLongTermCache() if os.getenv("FUSION_SSD_LONGTERM_CACHE") else None
        self._last_update = time.time()

        print(f"[VirtualGPUHT] Initialized: GPU={self.use_gpu}, state_size={self.state_size}, max={self.max_threads}")

    def _has_gpu(self) -> bool:
        try:
            import torch
            if torch.cuda.is_available():
                return True
        except Exception:
            pass
        try:
            import cupy as cp
            return cp.cuda.is_available()
        except Exception:
            pass
        return False

    def _alloc_device_state(self):
        try:
            import torch
            if torch.cuda.is_available():
                return torch.zeros(self.state_size, dtype=torch.float32, device="cuda")
        except Exception:
            pass
        try:
            import cupy as cp
            if cp.cuda.is_available():
                return cp.zeros(self.state_size, dtype=cp.float32)
        except Exception:
            pass
        return np.zeros(self.state_size, dtype=np.float32)

    def _is_device_tensor(self, state) -> bool:
        try:
            import torch
            if isinstance(state, torch.Tensor):
                return state.is_cuda
        except Exception:
            pass
        try:
            import cupy as cp
            if isinstance(state, cp.ndarray):
                return True
        except Exception:
            pass
        return False

    def status(self):
        device_bytes = 0
        host_bytes = 0
        for state in self.vram.values():
            nbytes = getattr(state, "nbytes", None)
            if nbytes is None:
                try:
                    nbytes = state.numel() * state.element_size()
                except Exception:
                    nbytes = len(state) * 4 if hasattr(state, "__len__") else 0
            if self._is_device_tensor(state):
                device_bytes += nbytes
            else:
                host_bytes += nbytes
        return {
            "active_virtual_threads": len(self.vram),
            "vram_used_mb": round(device_bytes / (1024 * 1024), 2),
            "host_used_mb": round(host_bytes / (1024 * 1024), 2),
            "max_threads": self.max_threads,
            "state_size": self.state_size,
            "gpu_mode": self.use_gpu,
            "ssd_spill_enabled": self.ssd_cache is not None,
            "policy": "dedicated_vram_first",
        }

    def rebalance_to_dedicated_vram(self, target_ratio: float = 0.92, snap: dict | None = None) -> dict:
        """Migrate host states to dedicated VRAM; spill overflow to SSD not RAM."""
        migrated = 0
        spilled = 0
        if not self.use_gpu:
            self.use_gpu = True
        for tid, state in list(self.vram.items()):
            if self._is_device_tensor(state):
                continue
            host_arr = np.asarray(state, dtype=np.float32)
            try:
                import torch
                if torch.cuda.is_available():
                    self.vram[tid] = torch.from_numpy(host_arr).cuda()
                    migrated += 1
                    continue
            except Exception:
                pass
            if self.ssd_cache:
                self.ssd_cache.store(f"vthread_{tid}", host_arr)
                del self.vram[tid]
                spilled += 1
        added = 0
        if snap and snap.get("dedicated_vram", {}).get("free_mb", 0) > 0:
            free_mb = snap["dedicated_vram"]["free_mb"]
            bytes_per = max(self.state_size * 4, 1024)
            batch = min(512, int((free_mb * 0.75 * 1024 * 1024) / bytes_per))
            self.max_threads = max(self.max_threads, len(self.vram) + batch)
            for _ in range(batch):
                tid = self.allocate_virtual_thread()
                if tid is None:
                    break
                added += 1
        return {
            "migrated_to_vram": migrated,
            "spilled_to_ssd": spilled,
            "threads_added": added,
            "active": len(self.vram),
            "max_threads": self.max_threads,
        }

    def allocate_virtual_thread(self):
        if len(self.vram) >= self.max_threads:
            # Spill to SSD if possible
            if self.ssd_cache:
                return self.ssd_cache.allocate()
            return None
        tid = self.next_tid
        self.next_tid += 1
        state = self._alloc_device_state() if self.use_gpu else np.zeros(self.state_size, dtype=np.float32)
        self.vram[tid] = state
        return tid

    def free(self, tid):
        if tid in self.vram:
            del self.vram[tid]
        elif self.ssd_cache:
            self.ssd_cache.free(tid)

    def get_state(self, tid):
        if tid in self.vram:
            return self.vram[tid]
        if self.ssd_cache:
            return self.ssd_cache.load(tid)
        return None

    def update_state(self, tid, new_state):
        if tid in self.vram:
            self.vram[tid] = new_state
        elif self.ssd_cache:
            self.ssd_cache.store(tid, new_state)

def get_virtual_gpu_ht_cache():
    global _cache_instance
    if '_cache_instance' not in globals() or _cache_instance is None:
        _cache_instance = VirtualGPUHTCache()
    return _cache_instance

def gpu_virtual_energy_update(batch_tids, q_matrix=None):
    """Simulates energy / state update for a batch of virtual threads.
    This is where 'hyper-parallel' work happens (e.g. QUBO steps, annealing updates).
    """
    cache = get_virtual_gpu_ht_cache()
    start = time.perf_counter()
    updates = 0
    for tid in batch_tids:
        state = cache.get_state(tid)
        if state is None:
            continue
        if isinstance(state, np.ndarray):
            if q_matrix is not None and q_matrix.shape[0] == len(state):
                # Simple QUBO-like update
                delta = np.dot(q_matrix, state) * 0.01
                state = state + delta
            else:
                state = state * 0.995 + np.random.randn(len(state)).astype(np.float32) * 0.005
            cache.update_state(tid, state)
        else:
            # GPU tensor case
            try:
                import torch
                if q_matrix is not None:
                    q = torch.from_numpy(q_matrix).cuda() if cache.use_gpu else q_matrix
                    state = state + torch.matmul(q, state) * 0.01
                else:
                    state = state * 0.995 + torch.randn_like(state) * 0.005
                cache.update_state(tid, state)
            except:
                pass
        updates += 1
    return {
        "updated": updates,
        "time_ms": round((time.perf_counter() - start) * 1000, 3)
    }


class SSDLongTermCache:
    """Tier-2 cache on SSD for virtual thread states that don't fit in VRAM/RAM."""
    def __init__(self):
        self.base = Path(os.getenv("FUSION_SSD_LONGTERM_CACHE", "C:/FusionHero/LongTermCache"))
        self.base.mkdir(parents=True, exist_ok=True)
        self.meta = {}  # tid -> path

    def allocate(self):
        tid = max(self.meta.keys() or [0]) + 1
        path = self.base / f"vthread_{tid}.npy"
        self.meta[tid] = path
        np.save(path, np.zeros(256, dtype=np.float32))
        return tid

    def store(self, tid, data):
        path = self.meta.get(tid, self.base / f"vthread_{tid}.npy")
        np.save(path, np.asarray(data))
        self.meta[tid] = path

    def load(self, tid):
        path = self.meta.get(tid)
        if path and path.exists():
            return np.load(path)
        return None

    def free(self, tid):
        path = self.meta.pop(tid, None)
        if path and path.exists():
            path.unlink(missing_ok=True)

    def status(self):
        return {"ssd_threads": len(self.meta), "base_dir": str(self.base)}
