"""Bridge graph state to the existing classical QUBO/Ising solver.

This maps a :class:`~fusion_hero_os.meta.graph.GraphSnapshot` (plus optional
Hebbian association weights) into a QUBO matrix ``Q`` and solves
``min_x x^T Q x`` over ``x in {0,1}^n``.

Backends (selected in order, first available wins unless forced):

1. ``rust`` — the PyO3/rayon backend (``fusion_hero_os.engine.rust_backend``)
   when compiled.
2. ``qb_qubo`` — the repo's numba simulated-annealing solver (``qb_qubo`` at the
   repo root) when importable.
3. ``numpy`` — a dependency-free, deterministic simulated-annealing fallback
   implemented here (seeded ``numpy`` RNG). Always available.

This is **classical** optimisation. No quantum computing is used or claimed.

The result is auditable: it records objective value, the constraint terms, the
solver/backend actually used, the RNG seed, and an energy trace, plus the
source snapshot hash for provenance.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .graph import GraphSnapshot


class QUBOBridgeError(RuntimeError):
    pass


@dataclass(frozen=True)
class QUBOProblem:
    """A built QUBO instance with the node labelling and constraint metadata."""

    node_ids: list[str]
    Q: np.ndarray
    constraints: dict[str, object]
    source_snapshot: str

    @property
    def size(self) -> int:
        return len(self.node_ids)


@dataclass(frozen=True)
class QUBOResult:
    objective: float
    assignment: dict[str, int]
    solution_vector: list[int]
    backend: str
    seed: int
    steps: int
    energy_trace: list[float]
    constraints: dict[str, object]
    source_snapshot: str

    def to_dict(self) -> dict[str, object]:
        return {
            "objective": round(self.objective, 12),
            "assignment": dict(self.assignment),
            "solution_vector": list(self.solution_vector),
            "backend": self.backend,
            "seed": self.seed,
            "steps": self.steps,
            "energy_trace": [round(e, 12) for e in self.energy_trace],
            "constraints": dict(self.constraints),
            "source_snapshot": self.source_snapshot,
            "note": "Classical simulated annealing. Not quantum computing.",
        }


def build_qubo(
    snapshot: GraphSnapshot,
    *,
    selection_dimension: str,
    association: tuple[list[str], list[list[float]]] | None = None,
    cardinality: int | None = None,
    cardinality_penalty: float = 5.0,
) -> QUBOProblem:
    """Construct a QUBO from a graph snapshot.

    Objective: select a subset of nodes maximising per-node value (given by the
    ``selection_dimension``) plus pairwise association reward, i.e.

        minimise  -sum_i v_i x_i  -  sum_{i<j} A_ij x_i x_j  +  penalty*(sum_i x_i - k)^2

    The optional cardinality constraint softly enforces exactly ``k`` selected
    nodes via a quadratic penalty.
    """
    node_ids, dim_matrix = snapshot.node_matrix([selection_dimension])
    n = len(node_ids)
    if n == 0:
        raise QUBOBridgeError("cannot build QUBO from an empty graph")
    values = np.array([row[0] for row in dim_matrix], dtype=np.float64)

    Q = np.zeros((n, n), dtype=np.float64)
    # Linear term on the diagonal: reward high-value nodes (minimise -v_i x_i).
    for i in range(n):
        Q[i, i] += -values[i]

    # Pairwise association reward (symmetric, off-diagonal).
    if association is not None:
        assoc_ids, assoc_m = association
        pos = {nid: i for i, nid in enumerate(node_ids)}
        for ai, a in enumerate(assoc_ids):
            for bi, b in enumerate(assoc_ids):
                if ai < bi and a in pos and b in pos:
                    w = float(assoc_m[ai][bi])
                    if w != 0.0:
                        i, j = pos[a], pos[b]
                        Q[i, j] += -0.5 * w
                        Q[j, i] += -0.5 * w

    constraints: dict[str, object] = {"selection_dimension": selection_dimension}
    if cardinality is not None:
        # penalty * (sum x_i - k)^2 = penalty*(sum_i x_i(1-2k) + 2 sum_{i<j} x_i x_j + k^2)
        k = int(cardinality)
        p = float(cardinality_penalty)
        for i in range(n):
            Q[i, i] += p * (1.0 - 2.0 * k)
        for i in range(n):
            for j in range(i + 1, n):
                Q[i, j] += p
                Q[j, i] += p
        constraints["cardinality"] = k
        constraints["cardinality_penalty"] = p

    return QUBOProblem(
        node_ids=node_ids,
        Q=Q,
        constraints=constraints,
        source_snapshot=snapshot.content_hash,
    )


def energy(Q: np.ndarray, x: np.ndarray) -> float:
    x = np.asarray(x, dtype=np.float64)
    return float(x @ Q @ x)


def _anneal_numpy(
    Q: np.ndarray, *, steps: int, seed: int, T0: float = 2.0
) -> tuple[np.ndarray, float, list[float]]:
    """Deterministic pure-numpy simulated annealing (O(n) delta updates).

    Mirrors the semantics of ``qb_qubo.simulated_annealing`` but with no numba
    dependency, so it runs anywhere and is fully reproducible from ``seed``.
    """
    rng = np.random.default_rng(seed)
    n = Q.shape[0]
    Qf = np.ascontiguousarray(Q.astype(np.float64))
    x = rng.integers(0, 2, n).astype(np.int64)
    Qx = Qf @ x.astype(np.float64)
    e = float(x @ Qx)
    best_x = x.copy()
    best_e = e
    idxs = rng.integers(0, n, steps)
    us = rng.random(steps)
    trace: list[float] = []
    sample_every = max(1, steps // 50)
    for t in range(steps):
        T = T0 * (1.0 - t / steps) + 1e-3
        i = int(idxs[t])
        delta_x = 1 - 2 * int(x[i])
        delta_e = 2.0 * delta_x * Qx[i] + Qf[i, i] * delta_x * delta_x
        if delta_e < 0 or us[t] < np.exp(-delta_e / T):
            x[i] ^= 1
            e += delta_e
            Qx += Qf[:, i] * delta_x
            if e < best_e:
                best_e = e
                best_x = x.copy()
        if t % sample_every == 0:
            trace.append(best_e)
    trace.append(best_e)
    return best_x, best_e, trace


def _brute_force(Q: np.ndarray) -> tuple[np.ndarray, float]:
    n = Q.shape[0]
    best_x = None
    best_e = np.inf
    for mask in range(1 << n):
        x = np.array([(mask >> i) & 1 for i in range(n)], dtype=np.float64)
        e = float(x @ Q @ x)
        if e < best_e:
            best_e = e
            best_x = x
    return best_x.astype(np.int64), float(best_e)


def solve_qubo(
    problem: QUBOProblem,
    *,
    backend: str = "auto",
    seed: int = 7,
    steps: int = 4000,
) -> QUBOResult:
    """Solve a :class:`QUBOProblem`, returning an auditable :class:`QUBOResult`.

    ``backend`` in {"auto", "rust", "qb_qubo", "numpy", "brute"}. "auto" prefers
    rust, then qb_qubo, then numpy.
    """
    # The delta-energy update in ``_anneal_numpy`` (and the Ising mapping used
    # by the compiled backends) assumes a symmetric Q. For binary x the value
    # x^T Q x is invariant under Q -> (Q + Q^T)/2, so we symmetrise here rather
    # than rejecting asymmetric inputs. build_qubo already emits symmetric Q;
    # this makes externally-supplied problems safe too.
    Q = np.asarray(problem.Q, dtype=np.float64)
    if Q.ndim != 2 or Q.shape[0] != Q.shape[1]:
        raise QUBOBridgeError("Q must be a square 2D matrix")
    if not np.allclose(Q, Q.T, atol=1e-12):
        Q = 0.5 * (Q + Q.T)
    chosen = backend
    trace: list[float] = []

    def _via_numpy() -> tuple[np.ndarray, float, str]:
        x, e, tr = _anneal_numpy(Q, steps=steps, seed=seed)
        trace.extend(tr)
        return x, e, "numpy"

    if backend in ("brute",):
        x, e = _brute_force(Q)
        trace.append(e)
        chosen = "brute"
    elif backend in ("auto", "rust"):
        x = e = None  # type: ignore
        try:
            from fusion_hero_os.engine import rust_backend  # noqa: WPS433

            if rust_backend.AVAILABLE:
                res = rust_backend.parallel_anneal_rust(Q, steps=steps, base_seed=seed)
                x = np.asarray(res["solution"], dtype=np.int64)
                e = float(res["energy"])
                trace.extend([float(v) for v in res.get("traces", [[]])[0]] or [e])
                chosen = "rust"
        except Exception:
            x = None
        if x is None and backend == "rust":
            raise QUBOBridgeError("rust backend requested but unavailable")
        if x is None:
            x, e, chosen = _try_qb_qubo(Q, seed, steps, trace) or _via_numpy()
    elif backend == "qb_qubo":
        result = _try_qb_qubo(Q, seed, steps, trace)
        if result is None:
            raise QUBOBridgeError("qb_qubo backend requested but unavailable")
        x, e, chosen = result
    elif backend == "numpy":
        x, e, chosen = _via_numpy()
    else:
        raise QUBOBridgeError(f"unknown backend {backend!r}")

    solution = [int(v) for v in np.asarray(x).ravel()]
    assignment = {nid: solution[i] for i, nid in enumerate(problem.node_ids)}
    return QUBOResult(
        objective=float(e),
        assignment=assignment,
        solution_vector=solution,
        backend=chosen,
        seed=seed,
        steps=steps,
        energy_trace=trace,
        constraints=problem.constraints,
        source_snapshot=problem.source_snapshot,
    )


def _try_qb_qubo(Q, seed, steps, trace):
    """Attempt the repo's numba solver; return (x, e, 'qb_qubo') or None."""
    try:
        import qb_qubo  # noqa: WPS433
    except Exception:
        return None
    try:
        # qb_qubo uses a module-level seeded RNG; reseed for reproducibility.
        qb_qubo.rng = np.random.default_rng(seed)
        x, e = qb_qubo.simulated_annealing(np.asarray(Q, dtype=np.float64), steps=steps)
        trace.append(float(e))
        return np.asarray(x, dtype=np.int64), float(e), "qb_qubo"
    except Exception:
        return None
