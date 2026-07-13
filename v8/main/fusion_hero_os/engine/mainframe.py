# -*- coding: utf-8 -*-
"""
HEROIC CORE MAINFRAME — INTEGRAL VERSION (v5.25)
================================================
Zusammenführung von:
  1. High-Performance Solver Engine (SA-Kernel via Numba/NumPy)
  2. ClassicalBackend mit Pre-/Post-Solve-Audit-Hooks (hier definiert)
  3. Hook-/Stub-Layer:
       * SelfModify, MetaAnalysis — weiterhin PLATZHALTER (Vorschlags-Liste /
         Wort-Check), KEIN echtes Selbst-Modifikationssystem.
       * GenerationalEvolution — ECHTE (μ+λ)-Evolution über SA-Solver-Configs,
         bewertet via parallel_anneal (Fitness = -energy), elitär & monoton.
  4. AuditAgent-Gateway; "EudaimoniaGuard" = einfache Grenzwertprüfung der
     Matrix/Energie (NaN/Inf + Betragsschwellen), keine inhaltliche Garantie.
"""

import time
import os
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from numba import jit
from abc import ABC, abstractmethod

# Globaler Zufallsgenerator für deterministische Heuristiken
rng = np.random.default_rng(7)

# Wiederverwendbarer Thread-Pool je Worker-Anzahl: spart den Thread-Spawn-Overhead
# bei vielen kleinen Läufen (GUI/Sweep/Auto-Feeder). Schließt sich beim Prozessende.
_POOL = {}


def _get_pool(workers):
    ex = _POOL.get(workers)
    if ex is None:
        ex = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="anneal")
        _POOL[workers] = ex
    return ex

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
                    base_seed=0, workers=None, backend="numba"):
    """Multi-Start Simulated Annealing über alle logischen Kerne (Hyperthreading).

    Startet `n_restarts` unabhängige SA-Läufe parallel in Threads (echte
    Mehrkern-Nutzung dank `nogil`) und behält die beste Lösung. Liefert zusätzlich
    pro Restart einen Energie-Konvergenz-Trace für die Visualisierung.

    backend: "numba" (Default), "rust" (PyO3-Kernel, falls gebaut) oder "auto"
    (rust wenn verfügbar, sonst numba).

    Rückgabe: dict mit solution, energy, energies[], traces[][], trace_steps[],
    best_restart, n_restarts, workers, runtime_seconds (+ ggf. backend).
    """
    if backend in ("rust", "auto"):
        rb = None
        try:
            from fusion_hero_os.engine import rust_backend as rb  # Paket-Pfad (kanonisch)
        except Exception:  # noqa: BLE001
            try:
                from engine import rust_backend as rb  # Legacy top-level Layout
            except Exception:  # noqa: BLE001
                try:
                    import rust_backend as rb           # als Skript aus engine/ gestartet
                except Exception:  # noqa: BLE001
                    rb = None
        if rb is not None and getattr(rb, "AVAILABLE", False):
            return rb.parallel_anneal_rust(Q, steps=steps, T0=T0, n_restarts=n_restarts,
                                           n_samples=n_samples, base_seed=base_seed)
        if backend == "rust":
            raise RuntimeError("backend='rust' angefordert, aber 'rust_engine' ist nicht gebaut "
                               "(cd rust_engine && maturin develop --release).")
        # backend == "auto": still auf numba zurückfallen

    n = Q.shape[0]
    Qf = np.ascontiguousarray(Q.astype(np.float64))
    if n_restarts is None:
        n_restarts = os.cpu_count() or 4
    if workers is None:
        workers = os.cpu_count() or 4
    seeds = [base_seed + k for k in range(n_restarts)]

    t0 = time.time()
    ex = _get_pool(workers)  # wiederverwendeter Pool statt Neuanlage pro Aufruf
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
        "backend": "numba",
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
    """PLATZHALTER-STUB. Registriert Audit-Hooks und kann Modifikations-
    Vorschläge in einer Liste sammeln. Wendet NICHTS an — es findet keine
    echte Selbst-Modifikation des Codes statt (bewusst, aus Sicherheitsgründen)."""
    def __init__(self):
        self.modification_history = []
        self.audit_hooks = {}

    def register_audit_hook(self, name: str, func):
        self.audit_hooks[name] = func

class GenerationalEvolutionProtocolCoreModule:
    """ECHTE (μ+λ)-Evolution über SA-Solver-Konfigurationen.

    Genom = (steps, T0, n_restarts) — die Stellschrauben von `parallel_anneal`.
    Fitness eines Genoms = -energy des besten parallel_anneal-Laufs auf einem
    FESTEN, symmetrischen Ziel-QUBO (erzeugt via `make_Q`, das genau die vom
    SA-Kernel mit Faktor 2.0 erwarteten symmetrischen Matrizen liefert).
    Negatives Vorzeichen, weil parallel_anneal MINIMIERT (niedrigere Energie =
    besser), die Evolution aber MAXIMIERT.

    Selektion: elitäres (μ+λ). Pro Generation werden λ mutierte Nachkommen
    bewertet, mit den μ Eltern (deren Fitness gecacht ist) zusammengeführt und
    die besten μ behalten. Da die Eltern mit ihrem gecachten Fitnesswert im Pool
    bleiben, ist die beste Fitness über die Generationen MONOTON NICHT-FALLEND —
    die Elite kann nie schlechter werden.

    Import-sicher: keine Top-Level-Seiteneffekte; das Ziel-QUBO und die
    Startpopulation werden erst beim ersten `run_generation()` lazy erzeugt.
    """

    # Genom-Grenzen (min, max) je Gen — Mutationen werden hierauf geclippt.
    BOUNDS = {
        "steps": (200, 20000),
        "T0": (0.1, 8.0),
        "n_restarts": (1, max(1, os.cpu_count() or 4)),
    }

    def __init__(self, target_Q=None, n=14, mu=4, lam=8, seed=12345, init_genome=None):
        self.mu = int(mu)
        self.lam = int(lam)
        self.generation = 0
        self.fitness_history = []        # beste Fitness je Generation (monoton ↑)
        self.mean_fitness_history = []   # mittlere Elite-Fitness je Generation
        self.best_genome = None
        self.best_fitness = -np.inf
        # Eigener, reproduzierbarer RNG — entkoppelt vom Modul-globalen `rng`.
        self._rng = np.random.default_rng(seed)
        self._n = int(n)
        self._target_Q = None if target_Q is None else np.asarray(target_Q, dtype=np.float64)
        # Optionales Seeding: Startpopulation um dieses Genom herum (sonst zufällig).
        self._init_genome = None if init_genome is None else self._clip(dict(init_genome))
        self.population = None           # lazy: Liste[(genome_dict, fitness)]

    # ---------- Genom-Helfer ----------
    def _clip(self, genome):
        s_lo, s_hi = self.BOUNDS["steps"]
        t_lo, t_hi = self.BOUNDS["T0"]
        r_lo, r_hi = self.BOUNDS["n_restarts"]
        genome["steps"] = int(np.clip(round(float(genome["steps"])), s_lo, s_hi))
        genome["T0"] = float(np.clip(float(genome["T0"]), t_lo, t_hi))
        genome["n_restarts"] = int(np.clip(round(float(genome["n_restarts"])), r_lo, r_hi))
        return genome

    def _random_genome(self):
        s_lo, s_hi = self.BOUNDS["steps"]
        t_lo, t_hi = self.BOUNDS["T0"]
        r_lo, r_hi = self.BOUNDS["n_restarts"]
        return self._clip({
            "steps": int(self._rng.integers(s_lo, s_hi + 1)),
            "T0": float(self._rng.uniform(t_lo, t_hi)),
            "n_restarts": int(self._rng.integers(r_lo, r_hi + 1)),
        })

    def _mutate(self, parent):
        """Gauß-Rauschen relativ zur Spannweite je Gen, anschließend geclippt."""
        child = dict(parent)
        s_lo, s_hi = self.BOUNDS["steps"]
        t_lo, t_hi = self.BOUNDS["T0"]
        r_lo, r_hi = self.BOUNDS["n_restarts"]
        child["steps"] += self._rng.normal(0.0, 0.15 * (s_hi - s_lo))
        child["T0"] += self._rng.normal(0.0, 0.15 * (t_hi - t_lo))
        child["n_restarts"] += self._rng.normal(0.0, 0.15 * (r_hi - r_lo))
        return self._clip(child)

    def _target(self):
        """Festes, symmetrisches Ziel-QUBO (einmalig erzeugt, dann gecacht)."""
        if self._target_Q is None:
            self._target_Q = make_Q(self._n, submodular=False, scale=2.0)
        return self._target_Q

    def _fitness(self, genome):
        """Fitness = -energy des besten parallel_anneal-Laufs für dieses Genom.

        Festes Q + fester base_seed => deterministisch je Genom, damit Fitness
        über Generationen vergleichbar bleibt."""
        out = parallel_anneal(self._target(), steps=genome["steps"], T0=genome["T0"],
                              n_restarts=genome["n_restarts"], n_samples=2, base_seed=0)
        return -float(out["energy"])

    def _init_population(self):
        if self._init_genome is not None:
            genomes = [dict(self._init_genome)]
            genomes += [self._mutate(self._init_genome) for _ in range(self.mu - 1)]
        else:
            genomes = [self._random_genome() for _ in range(self.mu)]
        self.population = [(g, self._fitness(g)) for g in genomes]
        self.population.sort(key=lambda gf: gf[1], reverse=True)

    # ---------- Evolutionsschleife ----------
    def run_generation(self):
        """Führt EINE echte (μ+λ)-Generation aus und schreibt fitness_history fort."""
        if self.population is None:
            self._init_population()

        # λ Nachkommen aus zufällig gewählten Eltern erzeugen und bewerten.
        offspring = []
        for _ in range(self.lam):
            pidx = int(self._rng.integers(0, len(self.population)))
            child = self._mutate(self.population[pidx][0])
            offspring.append((child, self._fitness(child)))

        # (μ+λ): Eltern (gecachte Fitness) + Nachkommen, beste μ behalten.
        combined = self.population + offspring
        combined.sort(key=lambda gf: gf[1], reverse=True)
        self.population = combined[:self.mu]

        # Buchführung
        self.best_genome, self.best_fitness = self.population[0]
        self.generation += 1
        self.fitness_history.append(self.best_fitness)
        elite_mean = float(np.mean([f for _, f in self.population]))
        self.mean_fitness_history.append(elite_mean)

        return {
            "generation": self.generation,
            "status": "active",
            "best_fitness": self.best_fitness,
            "best_genome": dict(self.best_genome),
            "elite_mean_fitness": elite_mean,
        }

    def evolve(self, n_generations=10, verbose=False):
        """Bequeme Mehrgenerationen-Schleife. Liefert eine Zusammenfassung."""
        for _ in range(n_generations):
            status = self.run_generation()
            if verbose:
                g = status["best_genome"]
                print(f"  Gen {status['generation']:>2}: best_fitness={status['best_fitness']:.4f} "
                      f"(E={-status['best_fitness']:.4f}) | elite_mean={status['elite_mean_fitness']:.4f} "
                      f"| Genom steps={g['steps']}, T0={g['T0']:.3f}, restarts={g['n_restarts']}")
        return {
            "generations": self.generation,
            "best_fitness": self.best_fitness,
            "best_genome": dict(self.best_genome) if self.best_genome else None,
            "fitness_history": list(self.fitness_history),
            "mean_fitness_history": list(self.mean_fitness_history),
        }

class CriticalMetaAnalysisCoreModule:
    """PLATZHALTER-STUB. Prüft per Substring auf "immer"/"nie" als grobe
    Heuristik. Keine echte Meta-Analyse — nur ein einfacher Wort-Check."""
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
        # Leichter Lauf-Zähler nur für die Anzeige — bewusst ENTKOPPELT von der
        # evolutionären Optimierung (self.evolution.evolve(...)), damit ein
        # gesicherter Solve nicht versehentlich eine ganze (μ+λ)-Generation auslöst.
        self._run_index = 0

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
        """Führt einen geschützten, auditierten Solver-Lauf aus.

        Hinweis: Das ist EIN einzelner Solve durch die Audit-Layer — nicht die
        evolutionäre Optimierung. Die echte (μ+λ)-Evolution liegt in
        self.evolution.evolve(...)."""
        self._run_index += 1
        print(f"\n[CORE MAINFRAME] Starte gesicherten Lauf {self._run_index}...")

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
        self._run_index += 1
        n_eff = n_restarts or os.cpu_count() or 4
        print(f"\n[CORE MAINFRAME] Starte parallelen Lauf {self._run_index} "
              f"({n_eff} Restarts / {os.cpu_count()} Kerne)...")
        Q = np.asarray(problem_matrix, dtype=np.float64)

        # Layer 1: Pre-Solve Audit (epistemische Hygiene)
        self.audit_agent.execute_hook("before_solve",
                                      {"matrix_Q": Q, "timestamp": time.time()})

        out = parallel_anneal(Q, steps=steps, T0=T0,
                              n_restarts=n_restarts, n_samples=n_samples, backend="auto")

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

    # 5. ECHTE (mu+lambda)-Evolution ueber SA-Solver-Konfigurationen
    print("\n" + "=" * 80)
    print("GENERATIONELLE EVOLUTION  ((mu+lambda) ueber SA-Configs, Fitness = -energy)")
    print("=" * 80)
    # Groesseres Ziel-QUBO (n=120): hier zahlt die Solver-Konfiguration wirklich --
    # schwache Configs (wenig steps/restarts) finden das Optimum NICHT. Start von einer
    # bewusst BILLIGEN Config (steps=300, restarts=1), damit die Evolution sichtbar
    # staerkere Configs hochzuechtet, statt direkt im Optimum zu starten.
    evo = GenerationalEvolutionProtocolCoreModule(
        n=120, mu=4, lam=8, seed=2025,
        init_genome={"steps": 300, "T0": 0.4, "n_restarts": 1},
    )
    summary = evo.evolve(n_generations=10, verbose=True)

    hist = summary["fitness_history"]
    print("-" * 80)
    print(f"Fitness-Verlauf (beste je Generation): {[round(f, 4) for f in hist]}")
    g = summary["best_genome"]
    print(f"Bestes Genom:  steps={g['steps']}, T0={g['T0']:.3f}, n_restarts={g['n_restarts']}")
    print(f"Beste Fitness: {summary['best_fitness']:.6f}  (min. Energie E={-summary['best_fitness']:.6f})")

    # Verifikation: elitaere Selektion => beste Fitness darf nie zurueckfallen.
    monoton = all(hist[i + 1] >= hist[i] for i in range(len(hist) - 1))
    print(f"Monoton nicht-fallende Elite-Fitness ueber {len(hist)} Generationen: "
          f"{'JA (verifiziert)' if monoton else 'NEIN -- REGRESSION!'}")
    print("=" * 80)
    assert monoton, "Elite-Fitness ist zurueckgefallen -- (mu+lambda)-Elitismus verletzt!"
