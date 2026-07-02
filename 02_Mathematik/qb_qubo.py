# -*- coding: utf-8 -*-
"""
QUBO-Architektur der q/b-Beziehung  —  Optimierte Version
===========================================================
Optimierungen:
  1. make_Q: vollstaendig vektorisiert mit NumPy-Broadcasting
  2. brute_force_min: Batch-Auswertung via (X @ Q * X).sum(axis=1) (BLAS-beschleunigt)
  3. greedy_fix: Integer-Masken, keine Float-Konvertierung im Hot-Loop
  4. local_search: Energie-Delta-Analytik (O(n) pro Iteration statt O(n^2))
  5. simulated_annealing: Integer-Operationen, fewer copies
  6. qubo_to_ising: unveraendert (bereits vektorisiert)

Supersymmetrie-Erweiterung (coevolutionär mit v2-beta Pipeline + MasterSeed Propagation + Timespace Geometry, Stand 29.06.2026):
Zukünftig: gepaarte Variablen / Superpartner-Modi (z.B. Stabilitäts-Modus ↔ Evolutions-Modus) in der Energy-Funktion,
sodass QUBO-Lösungen supersymmetrisch invariant unter Partner-Transformation bleiben (Erhalt von Eudaimonia / Fidelity).
Erste Implementierung in nächster Iteration via erweiterte make_Q oder Post-Processing.
"""
import os
import time
import numpy as np
import itertools
from concurrent.futures import ThreadPoolExecutor
from numba import jit


rng = np.random.default_rng(7)


def _parallel_workers(override=None):
    if override is not None and override > 0:
        return override
    return os.cpu_count() or 4 if os.getenv("FUSION_HYPERTHREADING", "1") != "0" else 1


@jit(nopython=True, cache=True, fastmath=True)
def _batch_energy_numba(Q, X):
    n = Q.shape[0]
    batch = X.shape[0]
    out = np.empty(batch, dtype=np.float64)
    for b in range(batch):
        s = 0.0
        for i in range(n):
            for j in range(n):
                s += Q[i, j] * X[b, i] * X[b, j]
        out[b] = s
    return out


@jit(nopython=True, cache=True, fastmath=True)
def _energy_delta_numba(Qf, x, i):
    n = len(x)
    delta_x = 1 - 2 * x[i]
    de = 0.0
    for j in range(n):
        de += 2.0 * delta_x * Qf[j, i] * x[j]
    de += Qf[i, i] * delta_x * delta_x
    return de

# ---------- Kernfunktionen ----------

def energy(Q, x):
    """Evaluiere quadratische Form x^T Q x. x wird als float64 interpretiert."""
    x = np.asarray(x, dtype=np.float64)
    return float(x @ Q @ x)


def make_Q(n, submodular=False, scale=1.0):
    """Vektorisiert: Diagonale und Off-Diagonale in einem Rutsch."""
    Q = np.zeros((n, n), dtype=np.float64)
    r = rng.normal(0, scale, size=(n, n))
    Q += (r + r.T) / 2.0          # symmetrisch
    np.fill_diagonal(Q, rng.normal(0, scale, size=n))
    if submodular:
        # Off-Diagonale <= 0 erzwingen (submodular); Diagonale bleibt unveraendert.
        off = np.ones_like(Q) - np.eye(n)
        Q = np.where(off, -np.abs(Q), Q)
    return Q


def _batch_energy(Q, X):
    """Berechne x^T Q x fuer alle Zeilen in X (shape: batch x n)."""
    # X @ Q ergibt (batch x n); elementweise * X; sum ueber Achse 1
    return (X @ Q * X).sum(axis=1)


def brute_force_min(Q, chunk_size=512):
    """Vollstaendiger Brute-Force in BLAS-beschleunigten Batches."""
    n = Q.shape[0]
    best_x = None
    best_e = np.inf

    # Iterate in chunks to limit memory while keeping BLAS hot
    bits_iter = itertools.product([0, 1], repeat=n)
    while True:
        chunk = list(itertools.islice(bits_iter, chunk_size))
        if not chunk:
            break
        X = np.array(chunk, dtype=np.float64)     # shape: (batch, n)
        energies = _batch_energy(Q, X)
        min_idx = energies.argmin()
        if energies[min_idx] < best_e:
            best_e = energies[min_idx]
            best_x = chunk[min_idx]

    return np.array(best_x, dtype=np.int64), float(best_e)


def greedy_fix(Q, order):
    """Greedy-Fix mit analytischem Energie-Delta (keine Matrizenmultiplikation im Hot-Loop)."""
    n = Q.shape[0]
    x = np.full(n, -1, dtype=np.int8)           # -1 = ungesetzt
    Qf = Q.astype(np.float64)
    x_filled = np.zeros(n, dtype=np.float64)    # 0 fuer ungesetzt
    Qx = np.zeros(n, dtype=np.float64)          # Q @ x_filled
    current_e = 0.0

    for i in order:
        # delta_e = E(x mit x_i=1) - E(x mit x_i=0)
        # Da x_filled[i] == 0: delta_e = Q[i,i] + 2 * (Q @ x_filled)[i]
        delta_e = Qf[i, i] + 2.0 * Qx[i]
        if delta_e < 0:
            x[i] = 1
            x_filled[i] = 1.0
            Qx += Qf[:, i]                       # O(n) Vektoraddition
            current_e += delta_e
        else:
            x[i] = 0

    # Falls noch -1 uebrig (sollte nicht vorkommen, aber sicherheitshalber):
    x_final = np.where(x < 0, 0, x).astype(np.float64)
    final_e = float(x_final @ Qf @ x_final)
    return x.astype(np.int64), final_e


def local_search(Q, x0=None, iters=500):
    """Single-Bit-Flip mit Energie-Delta (O(n) pro Iteration statt O(n^2))."""
    if x0 is None:
        x0 = rng.integers(0, 2, Q.shape[0])
    x = np.array(x0, dtype=np.int64).copy()
    Qf = Q.astype(np.float64)
    Qx = (Qf @ x.astype(np.float64))            # (Qx)_i = sum_j Q_{ij} x_j
    e = float(x @ Qx)

    for _ in range(iters):
        improved = False
        for i in range(len(x)):
            # Flippe x_i: delta_x = 1 - 2*x_i  (1 wenn 0->1, -1 wenn 1->0)
            delta_x = 1 - 2 * x[i]
            delta_e = 2.0 * delta_x * Qx[i] + Q[i, i] * delta_x * delta_x
            if delta_e < -1e-12:
                x[i] = 1 - x[i]
                e += delta_e
                # Qx akualisieren: (Q @ x')_j = (Q @ x)_j + Q_{j,i} * (new_x_i - old_x_i)
                Qx += Qf[:, i] * delta_x
                improved = True
        if not improved:
            break
    return x.astype(np.int64), float(e)


@jit(nopython=True, cache=True, fastmath=True)
def _simulated_annealing_kernel(Qf, steps, T0, n, initial_x, random_indices, random_floats):
    """JIT SA-Core: O(n) Delta-Evaluation pro Flip."""
    x = initial_x.copy()
    Qx = np.zeros(n, dtype=np.float64)
    e = 0.0
    for i in range(n):
        acc = 0.0
        for j in range(n):
            acc += Qf[i, j] * x[j]
        Qx[i] = acc
        e += acc * x[i]
    best_x = x.copy()
    best_e = e
    for t in range(steps):
        T = T0 * (1.0 - t / steps) + 1e-3
        i = random_indices[t]
        delta_x = 1 - 2 * x[i]
        delta_e = 2.0 * delta_x * Qx[i] + Qf[i, i] * delta_x * delta_x
        if delta_e < 0 or random_floats[t] < np.exp(-delta_e / T):
            x[i] ^= 1
            e += delta_e
            for j in range(n):
                Qx[j] += Qf[j, i] * delta_x
            if e < best_e:
                best_e = e
                for j in range(n):
                    best_x[j] = x[j]
    return best_x, best_e


@jit(nopython=True, nogil=True, cache=True, fastmath=True)
def _sa_kernel_trace(Qf, steps, T0, n, initial_x, random_indices, random_floats,
                     trace_steps, trace_out):
    x = initial_x.copy()
    Qx = np.zeros(n, dtype=np.float64)
    e = 0.0
    for i in range(n):
        acc = 0.0
        for j in range(n):
            acc += Qf[i, j] * x[j]
        Qx[i] = acc
        e += acc * x[i]
    best_x = x.copy()
    best_e = e
    n_samples = trace_steps.shape[0]
    sidx = 0
    for t in range(steps):
        T = T0 * (1.0 - t / steps) + 1e-3
        i = random_indices[t]
        delta_x = 1 - 2 * x[i]
        delta_e = 2.0 * delta_x * Qx[i] + Qf[i, i] * delta_x * delta_x
        if delta_e < 0 or random_floats[t] < np.exp(-delta_e / T):
            x[i] ^= 1
            e += delta_e
            for j in range(n):
                Qx[j] += Qf[j, i] * delta_x
            if e < best_e:
                best_e = e
                for j in range(n):
                    best_x[j] = x[j]
        while sidx < n_samples and trace_steps[sidx] == t:
            trace_out[sidx] = best_e
            sidx += 1
    while sidx < n_samples:
        trace_out[sidx] = best_e
        sidx += 1
    return best_x, best_e


def simulated_annealing(Q, steps=4000, T0=2.0):
    """SA mit jittetem Kernel und O(n) Energie-Delta-Updates."""
    n = Q.shape[0]
    Qf = Q.astype(np.float64)
    initial_x = rng.integers(0, 2, n).astype(np.int64)
    random_indices = rng.integers(0, n, steps).astype(np.int64)
    random_floats = rng.random(steps).astype(np.float64)
    bx, be = _simulated_annealing_kernel(Qf, steps, T0, n, initial_x, random_indices, random_floats)
    return bx.astype(np.int64), float(be)


def _anneal_one(Qf, steps, T0, n, seed, n_samples):
    r = np.random.default_rng(seed)
    initial_x = r.integers(0, 2, n).astype(np.int64)
    random_indices = r.integers(0, n, steps).astype(np.int64)
    random_floats = r.random(steps).astype(np.float64)
    trace_steps = np.linspace(0, max(steps - 1, 0), n_samples).astype(np.int64)
    trace_out = np.empty(n_samples, dtype=np.float64)
    bx, be = _sa_kernel_trace(Qf, steps, T0, n, initial_x, random_indices,
                              random_floats, trace_steps, trace_out)
    return bx, be, trace_out


def parallel_anneal(Q, steps=8000, T0=2.0, n_restarts=None, n_samples=60,
                    base_seed=0, workers=None):
    """Multi-Start SA über alle logischen Kerne (Hyperthreading, nogil)."""
    n = Q.shape[0]
    Qf = np.ascontiguousarray(Q.astype(np.float64))
    n_restarts = n_restarts or _parallel_workers()
    workers = workers or _parallel_workers()
    seeds = [base_seed + k for k in range(n_restarts)]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(lambda s: _anneal_one(Qf, steps, T0, n, s, n_samples), seeds))
    runtime = time.time() - t0
    energies = [float(e) for _, e, _ in results]
    best_idx = int(np.argmin(energies))
    best_x, best_e, _ = results[best_idx]
    trace_steps = np.linspace(0, max(steps - 1, 0), n_samples).astype(np.int64)
    return {
        "solution": np.asarray(best_x, dtype=np.int64),
        "energy": float(best_e),
        "energies": energies,
        "best_restart": best_idx,
        "traces": [t.tolist() for _, _, t in results],
        "trace_steps": trace_steps.tolist(),
        "n_restarts": n_restarts,
        "workers": workers,
        "runtime_seconds": runtime,
    }


def warmup_kernels():
    Q = make_Q(4, scale=1.0)
    simulated_annealing(Q, steps=50, T0=1.0)
    parallel_anneal(Q, steps=50, n_restarts=2, n_samples=4)
    return True


def qubo_to_ising(Q):
    """x_i=(1+s_i)/2 -> H(s)=sum J_ij s_i s_j + sum h_i s_i + const."""
    n = Q.shape[0]
    a = np.diag(Q).copy()
    B = Q.copy()
    np.fill_diagonal(B, 0.0)
    J = B / 4.0
    h = a / 2.0 + B.sum(axis=1) / 2.0
    const = a.sum() / 2.0 + B[np.triu_indices(n, 1)].sum() / 2.0
    return J, h, const


def ising_energy(J, h, const, s):
    s = np.asarray(s, dtype=np.float64)
    return float(s @ J @ s + h @ s + const)


# ==================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  QUBO-ARCHITEKTUR DER q/b-BEZIEHUNG  —  Optimierte Version")
    print("=" * 60)

    # Optimierungsvergleich
    print("\n[Benchmark] Original vs. Optimiert")
    import time as _time

    n = 12
    Q = make_Q(n, submodular=False, scale=1.0)
    Q_bf = Q.copy()  # identische Matrix fuer Brute-Force und SA
    Q_sa = Q.copy()

    start = _time.perf_counter()
    bx, be = brute_force_min(Q_bf)
    t_bf = _time.perf_counter() - start
    print(f"\n[1] Grundzustand (Brute-Force Batch, n={n}): {t_bf*1000:.2f} ms  E*={be:.4f}")

    # --- Simulated Annealing ---
    for steps in [4000, 8000]:
        start = _time.perf_counter()
        sx, se = simulated_annealing(Q_sa, steps=steps)
        t_sa = _time.perf_counter() - start
        match = abs(be - se) < 1e-6
        print(f"    SA steps={steps}: {t_sa*1000:.2f} ms  E={se:.4f}  match={match}")

    # --- Pfadabhaengigkeit (Greedy) ---
    print("\n[2] Pfadabhaengigkeit (Greedy-Fix, optimiert)")
    diffs = 0
    trials = 200
    maxgap = 0.0
    start = _time.perf_counter()
    for _ in range(trials):
        Qd = make_Q(8, submodular=False)
        _, ef = greedy_fix(Qd, list(range(8)))
        _, eb = greedy_fix(Qd, list(reversed(range(8))))
        if abs(ef - eb) > 1e-9:
            diffs += 1
            maxgap = max(maxgap, abs(ef - eb))
    t_greedy_total = _time.perf_counter() - start
    print(f"    200x greedy(n=8): {t_greedy_total*1000:.2f} ms")
    print(f"    greedy(vorwaerts) != greedy(rueckwaerts) in {diffs}/{trials} Faellen (max Gap {maxgap:.3f})")

    # --- Submodularitaetstest ---
    print("\n[3] Submodularitaet als Kompatibilitaet ~")
    def success_rate(submod, trials=300, n=10):
        ok = 0
        for _ in range(trials):
            Qs = make_Q(n, submodular=submod)
            gx, ge = brute_force_min(Qs)
            x0 = rng.integers(0, 2, n)
            _, le = local_search(Qs, x0)
            if abs(le - ge) < 1e-6:
                ok += 1
        return ok / trials * 100

    start = _time.perf_counter()
    sr_sub = success_rate(True)
    sr_gen = success_rate(False)
    t_search = _time.perf_counter() - start
    print(f"    lokale Suche trifft Grundzustand (n=10, 300 Trials):")
    print(f"      submodular:  {sr_sub:.1f}%   in {t_search*1000:.1f} ms")
    print(f"      allgemein:   {sr_gen:.1f}%")

    # --- Ising-Bruecke ---
    print("\n[4] QUBO <-> Ising-Bruecke")
    Qb = make_Q(6)
    J, h, c = qubo_to_ising(Qb)
    okmap = True
    start = _time.perf_counter()
    for _ in range(2000):
        x = rng.integers(0, 2, 6)
        s = 2 * x - 1
        if abs(energy(Qb, x) - ising_energy(J, h, c, s)) > 1e-9:
            okmap = False
            break
    t_map = _time.perf_counter() - start
    print(f"    E_QUBO(x) == E_Ising fuer 2000 Tests: {okmap}  ({t_map*1000:.1f} ms)")
    print("=" * 60)
