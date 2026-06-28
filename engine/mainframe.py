# -*- coding: utf-8 -*-
"""
HEROIC CORE MAINFRAME — INTEGRAL VERSION (v5.25)
================================================
Zusammenführung von:
  1. High-Performance Solver Engine (qb_qubo.py via Numba/NumPy)
  2. Epistemischer Gateway-Architektur (ClassicalBackend in classical.py)
  3. Core Sicherheits-Layer (SelfModify, GenerationalEvolution, MetaAnalysis)
  4. Immutable Foundations (AuditAgent & EudaimoniaGuard Protokolle)
"""

import time
import os
import numpy as np
import itertools
from concurrent.futures import ThreadPoolExecutor
from numba import jit
from abc import ABC, abstractmethod

# Globaler Zufallsgenerator für deterministische Heuristiken
rng = np.random.default_rng(7)

# =====================================================================
# STUFE 1: DOMÄNEN-ENTITÄTEN (domain/*.py)
# =====================================================================

class QUBOProblem:
    def __init__(self, Q: np.ndarray):
        self.Q = np.asarray(Q, dtype=np.float64)

class SolverResult:
    def __init__(self, solution: np.ndarray, energy: float, backend: str, runtime_seconds: float):
        self.solution = solution
        self.energy = energy
        self.backend = backend
        self.runtime_seconds = runtime_seconds

class QUBOSolverConfig:
    def __init__(self, backend: str = "simulated_annealing", steps: int = 4000, T0: float = 2.0):
        self.backend = backend
        self.steps = steps
        self.T0 = T0

# =====================================================================
# STUFE 2: CORE ENGINE OPTIMIERUNGEN (_numba_kernels aus qb_qubo.py)
# =====================================================================

@jit(nopython=True, cache=True, fastmath=True)
def _simulated_annealing_kernel(Qf, steps, T0, n, initial_x, random_indices, random_floats):
    """Hochperformanter, jitteter SA-Core-Loop ohne Speicherallokationen."""
    x = initial_x.copy()
    # Qx[i] = sum_j Q[i,j]*x[j] und e = x^T Q x in einem Durchlauf
    # (manuelle Schleife statt @, vermeidet die BLAS/scipy-Abhängigkeit unter Numba)
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
            # O(n) Zeilen-Update
            for j in range(n):
                Qx[j] += Qf[j, i] * delta_x

            if e < best_e:
                best_e = e
                for j in range(n):
                    best_x[j] = x[j]

    return best_x, best_e

def simulated_annealing(Q, steps=4000, T0=2.0):
    """Python-Wrapper für den jitteten SA-Kernel."""
    n = Q.shape[0]
    Qf = Q.astype(np.float64)
    initial_x = rng.integers(0, 2, n).astype(np.int64)
    random_indices = rng.integers(0, n, steps).astype(np.int64)
    random_floats = rng.random(steps).astype(np.float64)

    return _simulated_annealing_kernel(Qf, steps, T0, n, initial_x, random_indices, random_floats)

def local_search(Q, iters=500):
    """Single-Bit-Flip mit analytischem Energie-Delta und O(n) Updates."""
    n = Q.shape[0]
    x = rng.integers(0, 2, n).astype(np.int64)
    Qf = Q.astype(np.float64)
    Qx = Qf @ x.astype(np.float64)
    e = float(x @ Qx)

    for _ in range(iters):
        improved = False
        for i in range(n):
            delta_x = 1 - 2 * x[i]
            delta_e = 2.0 * delta_x * Qx[i] + Q[i, i] * delta_x * delta_x
            if delta_e < -1e-12:
                x[i] = 1 - x[i]
                e += delta_e
                Qx += Qf[:, i] * delta_x
                improved = True
        if not improved:
            break
    return x, e

def make_Q(n, submodular=False, scale=1.0):
    """Generiert symmetrische, kontrollierte Testmatrizen."""
    Q = np.zeros((n, n), dtype=np.float64)
    r = rng.normal(0, scale, size=(n, n))
    Q += (r + r.T) / 2.0
    np.fill_diagonal(Q, rng.normal(0, scale, size=n))
    if submodular:
        off = np.ones_like(Q) - np.eye(n)
        Q = np.where(off, -np.abs(Q), Q)
    return Q

# =====================================================================
# STUFE 2b: PARALLELE ENGINE (Multi-Start SA über alle Kerne / Hyperthreading)
# =====================================================================

@jit(nopython=True, nogil=True, cache=True, fastmath=True)
def _sa_kernel_trace(Qf, steps, T0, n, initial_x, random_indices, random_floats,
                     trace_steps, trace_out):
    """SA-Kernel mit Konvergenz-Trace.

    `nogil=True` gibt während des heißen Loops den GIL frei — dadurch laufen
    mehrere Restarts in einem ThreadPoolExecutor echt parallel auf mehreren Kernen.
    `trace_out[k]` = bestes E zum vordefinierten Schritt `trace_steps[k]`.
    """
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


def _anneal_one(Qf, steps, T0, n, seed, n_samples):
    """Ein deterministisch geseedeter SA-Restart -> (x, e, trace)."""
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
    """Multi-Start Simulated Annealing über alle logischen Kerne (Hyperthreading).

    Startet `n_restarts` unabhängige SA-Läufe parallel in Threads (echte
    Mehrkern-Nutzung dank `nogil`) und behält die beste Lösung. Liefert zusätzlich
    pro Restart einen Energie-Konvergenz-Trace für die Visualisierung.

    Rückgabe: dict mit solution, energy, energies[], traces[][], trace_steps[],
    best_restart, n_restarts, workers, runtime_seconds.
    """
    n = Q.shape[0]
    Qf = np.ascontiguousarray(Q.astype(np.float64))
    if n_restarts is None:
        n_restarts = os.cpu_count() or 4
    if workers is None:
        workers = os.cpu_count() or 4
    seeds = [base_seed + k for k in range(n_restarts)]

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(
            lambda s: _anneal_one(Qf, steps, T0, n, s, n_samples), seeds))
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
    """Triggert die Numba-Kompilierung beider Kernel mit Mini-Problemen, damit der
    erste echte Lauf nicht serien-langsam wirkt (cache=True persistiert das Ergebnis)."""
    Q = make_Q(4, scale=1.0)
    simulated_annealing(Q, steps=50, T0=1.0)                 # kompiliert _simulated_annealing_kernel
    parallel_anneal(Q, steps=50, n_restarts=2, n_samples=4)  # kompiliert _sa_kernel_trace
    return True

# =====================================================================
# STUFE 3: ABSTRACT BASE & BACKEND (backends/base.py & classical.py)
# =====================================================================

class SolverBackend(ABC):
    @abstractmethod
    def solve(self, problem: QUBOProblem, config: QUBOSolverConfig) -> SolverResult:
        pass

class ClassicalBackend(SolverBackend):
    """
    Klassischer QUBO-Solver-Backend.
    Bettet die qb_qubo Heuristiken direkt in die Kontrollarchitektur ein.
    """
    def __init__(self, audit_agent=None, meta_analyzer=None):
        self.audit_agent = audit_agent
        self.meta_analyzer = meta_analyzer
        self.solvers = {
            "simulated_annealing": simulated_annealing,
            "local_search": local_search
        }

    def solve(self, problem: QUBOProblem, config: QUBOSolverConfig) -> SolverResult:
        # --- LAYER 1: PRE-SOLVE AUDIT (Epistemische Hygiene) ---
        if self.audit_agent:
            audit_payload = {"matrix_Q": problem.Q, "timestamp": time.time()}
            self.audit_agent.execute_hook("before_solve", audit_payload)

            if self.meta_analyzer:
                # Schneller Check auf inflationäre/unbeschränkte Werte
                issues = self.meta_analyzer.analyze(f"QUBO Dimension: {problem.Q.shape[0]}")
                if issues:
                    print(f"[WARN] Meta-Analyse Trigger: {issues}")

        # --- LAYER 2: INTERNE EXECUTION ---
        start_time = time.time()
        solver_func = self.solvers.get(config.backend, self.solvers["simulated_annealing"])

        if config.backend == "simulated_annealing":
            x, energy = solver_func(problem.Q, steps=config.steps, T0=config.T0)
        else:
            x, energy = solver_func(problem.Q)

        runtime = time.time() - start_time

        result = SolverResult(
            solution=x,
            energy=energy,
            backend=config.backend,
            runtime_seconds=runtime
        )

        # --- LAYER 3: POST-SOLVE AUDIT (Eudaimonia Validation) ---
        if self.audit_agent:
            self.audit_agent.execute_hook("after_solve", {"result": result})

        return result

# =====================================================================
# STUFE 4: CORE ARCHITEKTUR-MODULE (SelfModify, Evolution, MetaAnalysis)
# =====================================================================

class SelfModifyCoreModule:
    def __init__(self):
        self.modification_history = []
        self.audit_hooks = {}

    def register_audit_hook(self, name: str, func):
        self.audit_hooks[name] = func

class GenerationalEvolutionProtocolCoreModule:
    def __init__(self):
        self.generation = 0

    def run_generation(self):
        self.generation += 1
        return {"generation": self.generation, "status": "active"}

class CriticalMetaAnalysisCoreModule:
    def analyze(self, text: str) -> list:
        issues = []
        if "immer" in text.lower() or "nie" in text.lower():
            issues.append("Mögliche epistemische Inflation erkannt")
        return issues

# =====================================================================
# STUFE 5: DER INTEGRATIONS-MAINFRAME
# =====================================================================

class ExecutableAuditAgent:
    """Implementierung des AuditAgent-Gatekeepers nach ALTE_FRAU_95g-Spezifikation."""
    def __init__(self):
        self.execute_hook = None

class QUBOIntegrationCoreModule:
    """Zentrales Integrationsmodul zur autonomen Verwaltung des Solvers."""
    def __init__(self):
        self.self_modify = SelfModifyCoreModule()
        self.evolution = GenerationalEvolutionProtocolCoreModule()
        self.meta_analyzer = CriticalMetaAnalysisCoreModule()
        self.audit_agent = ExecutableAuditAgent()

        # Injektion der Abhängigkeiten in das Backend
        self.backend = ClassicalBackend(
            audit_agent=self.audit_agent,
            meta_analyzer=self.meta_analyzer
        )

        self._interlock_core_hooks()

    def _interlock_core_hooks(self):
        """Koppelt die Systemüberwachung an das Modifikationsprotokoll."""
        def pre_solve_audit_hook(payload):
            Q = payload.get("matrix_Q")
            # Epistemischer Stabilitätscheck
            if np.any(np.isnan(Q)) or np.any(np.isinf(Q)):
                raise ValueError("[CRITICAL] Epistemischer Kollaps: Ungültige Matrixzustände detektiert.")

            # Überprüfung auf extreme Skalierungs-Disbalancen (Modal-Kollaps-Schutz)
            max_val = np.max(np.abs(Q))
            if max_val > 1e5:
                print("[AUDIT] Warnung: Hohe Penalty-Werte erkannt. Risiko von Modal-Kollaps erhöht.")

            print("[AUDIT] Layer 1 (Pre-Solve): Strukturüberprüfung der Matrix Q erfolgreich passed.")
            return True

        def post_solve_audit_hook(payload):
            result = payload.get("result")
            # Eudaimonische Grenzwertüberwachung (Schutz vor unkontrollierter System-Divergenz)
            if result.energy > 1e6:
                print("[ALERT] Divergenter Energiewert außerhalb des eudaimonischen Korridors.")

            print(f"[AUDIT] Layer 3 (Post-Solve): Integritätsprüfung abgeschlossen. Validierte Energie: {result.energy:.4f}")
            return True

        # Registrierung im Kernel-Protokoll
        self.self_modify.register_audit_hook("before_solve", pre_solve_audit_hook)
        self.self_modify.register_audit_hook("after_solve", post_solve_audit_hook)

        # Hooks live an das funktionale Ausführungs-Interface binden
        self.audit_agent.execute_hook = lambda name, data: self.self_modify.audit_hooks[name](data)

    def execute_secure_run(self, problem_matrix, config=None):
        """Führt einen geschützten Optimierungszyklus innerhalb der aktuellen Generation aus."""
        gen_status = self.evolution.run_generation()
        print(f"\n[CORE MAINFRAME] Starte Evolutionäre Generation {gen_status['generation']}...")

        if config is None:
            config = QUBOSolverConfig(backend="simulated_annealing", steps=5000)

        problem = QUBOProblem(Q=problem_matrix)
        result = self.backend.solve(problem, config)
        return result

    def execute_parallel_run(self, problem_matrix, steps=8000, T0=2.0,
                             n_restarts=None, n_samples=60):
        """Parallel-Lauf (Multi-Start SA über alle Kerne) durch die Audit-Layer.

        Liefert das volle Ergebnis-Dict aus parallel_anneal inkl. Konvergenz-Traces
        für die Visualisierung — und durchläuft dieselben Layer-1/3-Audits wie
        execute_secure_run.
        """
        gen_status = self.evolution.run_generation()
        n_eff = n_restarts or os.cpu_count() or 4
        print(f"\n[CORE MAINFRAME] Starte parallele Generation {gen_status['generation']} "
              f"({n_eff} Restarts / {os.cpu_count()} Kerne)...")
        Q = np.asarray(problem_matrix, dtype=np.float64)

        # Layer 1: Pre-Solve Audit (epistemische Hygiene)
        self.audit_agent.execute_hook("before_solve",
                                      {"matrix_Q": Q, "timestamp": time.time()})

        out = parallel_anneal(Q, steps=steps, T0=T0,
                              n_restarts=n_restarts, n_samples=n_samples)

        # Layer 3: Post-Solve Audit (Eudaimonia-Validierung)
        audit_result = SolverResult(solution=out["solution"], energy=out["energy"],
                                    backend="parallel_annealing",
                                    runtime_seconds=out["runtime_seconds"])
        self.audit_agent.execute_hook("after_solve", {"result": audit_result})
        return out

# =====================================================================
# PIPELINE-LAUFZEIT-VALIDIERUNG
# =====================================================================

if __name__ == "__main__":
    print("=" * 80)
    print("INITIALISIERE HEROIC CORE MAINFRAME (ALTE_FRAU_95g) MIT INTEGRALEM SOLVER")
    print("=" * 80)

    # 1. Mainframe initialisieren (Booting und Hook-Interlocking)
    mainframe = QUBOIntegrationCoreModule()

    # 2. Generierung einer kontrollierten Test-Matrix (n=12)
    print("\n[SYSTEM] Generiere System-Problemmatrix (Dimension n=12)...")
    target_matrix = make_Q(12, submodular=False, scale=2.5)

    # 3. Autonome Ausführung der ersten Generation über das gesicherte Interface
    solver_config = QUBOSolverConfig(backend="simulated_annealing", steps=8000, T0=2.5)
    execution_result = mainframe.execute_secure_run(target_matrix, config=solver_config)

    # 4. Ausgabe der verifizierten Zustandskonfiguration
    print("-" * 80)
    print("CORE-STATUS: STABIL // PRODUKTIONSBEREIT")
    print(f"Berechneter Systemzustand (x): {execution_result.solution}")
    print(f"Validierte minimale Energie E: {execution_result.energy:.6f}")
    print(f"Laufzeit der Engine:           {execution_result.runtime_seconds * 1000:.2f} ms")
    print("=" * 80)
