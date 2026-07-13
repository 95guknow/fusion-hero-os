import os
import json
import cupy as cp
import hashlib
from typing import Dict, Optional, Tuple

class CacheManager:
    def __init__(self, 
                 base_path: str = r"C:\FusionHero\QuboCache",
                 vram_cache_size: int = 50):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        self.vram_cache: Dict[str, Dict] = {}           # Problem-ID → arrays on GPU
        self.vram_cache_size = vram_cache_size

    def _get_problem_path(self, problem_id: str) -> str:
        return os.path.join(self.base_path, f"{problem_id}_problem.json")

    def _get_solution_path(self, problem_id: str) -> str:
        return os.path.join(self.base_path, f"{problem_id}_solution.json")

    # ====================== PROBLEM CACHING (bcache/SSD) ======================
    def save_problem(self, problem_id: str, Q: Dict, bias: Dict):
        path = self._get_problem_path(problem_id)
        # serialize tuple keys to str for json
        Q_serial = {f"{i},{j}": float(val) for (i, j), val in Q.items()}
        bias_serial = {str(i): float(v) for i, v in bias.items()}
        data = {"Q": Q_serial, "bias": bias_serial}
        with open(path, "w") as f:
            json.dump(data, f)

    def load_problem(self, problem_id: str) -> Optional[Tuple[Dict, Dict]]:
        path = self._get_problem_path(problem_id)
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            return data["Q"], data["bias"]
        return None

    # ====================== SOLUTION CACHING (SSD) ======================
    def save_solution(self, problem_id: str, result: Dict):
        path = self._get_solution_path(problem_id)
        with open(path, "w") as f:
            json.dump(result, f)

    def load_solution(self, problem_id: str) -> Optional[Dict]:
        path = self._get_solution_path(problem_id)
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return None

    # ====================== VRAM CACHING (GPU) ======================
    def preload_to_vram(self, problem_id: str, Q: Dict, bias: Dict, num_vars: int):
        """Loads Q-Matrix and bias to GPU VRAM (using CuPy for our env)"""
        if problem_id in self.vram_cache:
            return self.vram_cache[problem_id]

        Q_t = cp.zeros((num_vars, num_vars), dtype=cp.float32)
        for (i, j), val in Q.items():
            Q_t[i, j] = val
            Q_t[j, i] = val

        bias_t = cp.zeros(num_vars, dtype=cp.float32)
        for i, val in bias.items():
            bias_t[i] = val

        self.vram_cache[problem_id] = {"Q": Q_t, "bias": bias_t}

        # LRU-like limit
        if len(self.vram_cache) > self.vram_cache_size:
            oldest = next(iter(self.vram_cache))
            del self.vram_cache[oldest]

        return self.vram_cache[problem_id]

    def get_from_vram(self, problem_id: str):
        return self.vram_cache.get(problem_id)

# Backward compat for existing code
def get_qubo_cache_path(subpath: str = "") -> str:
    base = r"C:\FusionHero\QuboCache"
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, subpath) if subpath else base

def use_bcache_path(path: str) -> str:
    return get_qubo_cache_path(path)

def try_spill_to_vram(data: dict, tid: int = None):
    print(f"[VRAM-HOOK] Would cache for thread {tid} (using CacheManager now)")
    return False
