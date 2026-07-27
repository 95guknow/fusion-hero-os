"""Coupling / Jacobian analysis and fixed-point convergence checks.

Given a vector field ``F: R^n -> R^n`` describing how the meta-neural state
evolves (``x_{k+1} = F(x_k)``), we provide:

* :func:`jacobian_fd` — the Jacobian ``J_ij = dF_i/dx_j`` via central finite
  differences.
* :func:`spectral_radius` — ``rho(J) = max_i |lambda_i|``.
* :func:`is_contraction` — a Banach fixed-point *sufficient* condition: if an
  induced operator norm ``||J|| < 1`` on a region, ``F`` is a contraction there
  and has a unique fixed point to which iteration converges.
* :func:`iterate_to_fixed_point` — plain fixed-point iteration with a residual
  stopping rule.

Honesty
-------
The contractivity test is a **local, sufficient** condition. A spectral radius
below 1 indicates *local* linear stability of a fixed point; it does **not**
prove global convergence for a general nonlinear ``F``. We report the condition
that actually holds and never claim general nonlinear convergence without the
norm bound.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable

import numpy as np

VectorField = Callable[[np.ndarray], np.ndarray]


def jacobian_fd(F: VectorField, x: np.ndarray, *, eps: float = 1e-6) -> np.ndarray:
    """Central finite-difference Jacobian of ``F`` at ``x`` (shape n x n)."""
    x = np.asarray(x, dtype=np.float64)
    n = x.shape[0]
    f0 = np.asarray(F(x), dtype=np.float64)
    m = f0.shape[0]
    J = np.zeros((m, n), dtype=np.float64)
    for j in range(n):
        dx = np.zeros(n, dtype=np.float64)
        dx[j] = eps
        fp = np.asarray(F(x + dx), dtype=np.float64)
        fm = np.asarray(F(x - dx), dtype=np.float64)
        J[:, j] = (fp - fm) / (2.0 * eps)
    return J


def spectral_radius(J: np.ndarray) -> float:
    J = np.asarray(J, dtype=np.float64)
    eig = np.linalg.eigvals(J)
    return float(np.max(np.abs(eig))) if eig.size else 0.0


def operator_norm(J: np.ndarray, *, order: str = "2") -> float:
    """Induced operator norm. order in {'1', '2', 'inf', 'fro'}."""
    J = np.asarray(J, dtype=np.float64)
    if order == "1":
        return float(np.linalg.norm(J, 1))
    if order == "inf":
        return float(np.linalg.norm(J, np.inf))
    if order == "fro":
        return float(np.linalg.norm(J, "fro"))
    return float(np.linalg.norm(J, 2))


@dataclass(frozen=True)
class ContractionResult:
    is_contraction: bool
    lipschitz_bound: float  # the induced-norm bound used (||J||)
    spectral_radius: float
    norm_order: str

    def to_dict(self) -> dict:
        return {
            "is_contraction": self.is_contraction,
            "lipschitz_bound": round(self.lipschitz_bound, 12),
            "spectral_radius": round(self.spectral_radius, 12),
            "norm_order": self.norm_order,
            "note": (
                "Sufficient local condition (Banach). ||J||<1 => local contraction "
                "with a unique fixed point. Not a proof of global nonlinear convergence."
            ),
        }


def is_contraction(J: np.ndarray, *, norm_order: str = "inf") -> ContractionResult:
    """Banach sufficient contractivity test via an induced operator norm."""
    bound = operator_norm(J, order=norm_order)
    return ContractionResult(
        is_contraction=bound < 1.0,
        lipschitz_bound=bound,
        spectral_radius=spectral_radius(J),
        norm_order=norm_order,
    )


@dataclass(frozen=True)
class FixedPointResult:
    converged: bool
    iterations: int
    residual: float
    x: list[float]

    def to_dict(self) -> dict:
        return {
            "converged": self.converged,
            "iterations": self.iterations,
            "residual": round(self.residual, 12),
            "x": [round(v, 12) for v in self.x],
        }


def iterate_to_fixed_point(
    F: VectorField,
    x0: np.ndarray,
    *,
    tol: float = 1e-9,
    max_iter: int = 1000,
) -> FixedPointResult:
    """Fixed-point iteration ``x <- F(x)`` with residual stopping rule."""
    x = np.asarray(x0, dtype=np.float64).copy()
    residual = float("inf")
    it = 0
    for it in range(1, max_iter + 1):
        x_next = np.asarray(F(x), dtype=np.float64)
        residual = float(np.linalg.norm(x_next - x, np.inf))
        x = x_next
        if residual <= tol:
            return FixedPointResult(True, it, residual, x.tolist())
    return FixedPointResult(residual <= tol, it, residual, x.tolist())
