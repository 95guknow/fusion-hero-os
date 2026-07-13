"""QUBO problem representation."""

from __future__ import annotations

import numpy as np


class QUBOProblem:
    def __init__(self, Q: np.ndarray):
        # Preserve CuPy arrays when present (GPU path); otherwise coerce to float64.
        if hasattr(Q, "device") or "cupy" in str(type(Q)):
            self.Q = Q
        else:
            self.Q = np.asarray(Q, dtype=np.float64)