# ssd_longterm_cache.py
# Standalone SSD Long Term Cache for virtual HT spill-over
# Used when GPU/RAM cache is full

import os
from pathlib import Path
import numpy as np

class SSDLongTermCache:
    """Persistent cache on SSD (or fast storage) for long-term virtual thread states,
    activations, or large intermediate results.
    """
    def __init__(self, base_dir: str = None):
        # Prefer explicit path, then GDrive cold LongTermCache, then local C: fallback.
        if base_dir:
            root = Path(base_dir)
        elif os.getenv("FUSION_SSD_LONGTERM_CACHE"):
            root = Path(os.environ["FUSION_SSD_LONGTERM_CACHE"])
        else:
            root = None
            try:
                import sys
                _tools = Path(__file__).resolve().parents[2] / "tools"
                if str(_tools) not in sys.path:
                    sys.path.insert(0, str(_tools))
                from storage_policy import resolve_longterm_cache_root  # type: ignore

                resolved = resolve_longterm_cache_root()
                if resolved is not None:
                    root = resolved
            except Exception:
                root = None
            if root is None:
                root = Path("C:/FusionHero/LongTermCache")
        self.base = Path(root)
        self.base.mkdir(parents=True, exist_ok=True)
        self.index = {}  # key -> filepath

    def store(self, key: str, data: np.ndarray):
        path = self.base / f"{key}.npy"
        np.save(path, np.asarray(data))
        self.index[key] = path

    def load(self, key: str):
        path = self.index.get(key)
        if not path or not path.exists():
            path = self.base / f"{key}.npy"
            if path.exists():
                self.index[key] = path
            else:
                return None
        return np.load(path)

    def free(self, key: str):
        path = self.index.pop(key, None)
        if path and path.exists():
            path.unlink(missing_ok=True)

    def status(self):
        total_size = sum(p.stat().st_size for p in self.index.values() if p.exists())
        return {
            "cached_items": len(self.index),
            "total_size_mb": round(total_size / (1024*1024), 2),
            "base_dir": str(self.base)
        }

    def allocate(self, prefix="vht_"):
        # For compatibility with virtual HT
        key = f"{prefix}{len(self.index)}"
        self.store(key, np.zeros(256, dtype=np.float32))
        return key
