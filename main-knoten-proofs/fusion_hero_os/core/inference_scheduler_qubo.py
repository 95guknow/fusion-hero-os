# -*- coding: utf-8 -*-
"""
Inference-Scheduling-QUBO - v1 (Layer/Batch-Granularitaet, ehrliche Fassung)

Setzt die Peer-Review-Iteration vom 2026-07-05 um (QUBO fuer ternaeres
Inferenz-Scheduling), mit den Korrekturen aus der Repo-Kritik:

  * GRANULARITAET: Zuweisungseinheiten sind LAYER oder TOKEN-BATCHES, nicht
    einzelne Operationen — die Kernel-interne Optimierung (mpGEMM, TL1/TL2,
    I2_S in bitnet.cpp) ist fuer einen externen Scheduler unsichtbar und wird
    hier NICHT modelliert.
  * KONVENTION: Der Review-Einwand "Q muss symmetrisch sein" ist KEIN Satz —
    obere Dreiecksform ist gueltig, da x_i x_j = x_j x_i (nur J_ij + J_ji
    zaehlt). Der hiesige SA-Kernel (qb_qubo._sa_kernel_trace) setzt fuer seine
    O(n)-Delta-Updates allerdings symmetrisches Q voraus; build_qubo()
    liefert deshalb die symmetrisierte Form (J/2 auf beide Haelften).
  * SOLVER: repo-eigenes parallel_anneal (numba, Multi-Start-SA) — KEINE
    neal/dimod-Abhaengigkeit.

Modell (Zwei-Einheiten-Zuweisung, x_i in {0,1}: 0 = CPU, 1 = NPU):

    H(x) = sum_i [ c_npu_i * x_i + c_cpu_i * (1 - x_i) ]
         + sum_{i<j} [ p_npu_ij * x_i x_j  +  p_cpu_ij * (1-x_i)(1-x_j) ]

  c_*_i   : Kosten der Einheit i auf CPU bzw. NPU (z. B. gemessene ms).
  p_npu_ij: Contention-Strafe, wenn i UND j auf der NPU laufen (Bus/Speicher).
  p_cpu_ij: analog fuer CPU.

SATZ (exakte QUBO-Kodierung): Mit
    Q_ii     = c_npu_i - c_cpu_i - sum_{j != i} p_cpu_ij
    Q_ij     = (p_npu_ij + p_cpu_ij) / 2   fuer i != j (symmetrisiert)
    offset   = sum_i c_cpu_i + sum_{i<j} p_cpu_ij
gilt   H(x) = x^T Q x + offset   fuer ALLE x in {0,1}^n.

BEWEIS: (1-x_i)(1-x_j) = 1 - x_i - x_j + x_i x_j. Einsetzen und sortieren:
konstante Terme -> offset; lineare Terme (x_i = x_i^2 auf der Diagonalen):
c_npu_i - c_cpu_i aus den Einzelkosten, -sum_j p_cpu_ij aus den CPU-Paaren;
quadratische Terme: (p_npu_ij + p_cpu_ij) x_i x_j, im symmetrischen Q als
Q_ij + Q_ji = p_npu_ij + p_cpu_ij realisiert. QED.
(Verankert: tests/test_inference_scheduler_qubo.py, Registry
SCHED-QUBO-ENCODING-EXAKT.)

DESIGN-GARANTIE statt Heuristik-Hoffnung: solve_schedule() wertet IMMER auch
die Greedy-Supervisor-Heuristik aus und gibt die bessere der beiden Loesungen
zurueck. "Nie schlechter als Greedy" gilt damit BY CONSTRUCTION (Registry
SCHED-QUBO-NIE-SCHLECHTER-GREEDY) — wie oft SA strikt besser ist, wird
ehrlich mitgeliefert, aber nicht garantiert.

OFFEN bleibt (Registry QUBO-SCHEDULER-NUTZEN): ob das auf REALEN Workloads
(echte Latenz/Durchsatz statt synthetischer Kostenmodelle) messbar gewinnt.

Teil der 02_architecture Schicht.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import numpy as np

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from qb_qubo import parallel_anneal  # kanonische Kopie (QBQUBO-KOPIEN-SYNC)


@dataclass
class ScheduleProblem:
    """Ein Zuweisungsproblem in Layer/Batch-Granularitaet."""
    cost_cpu: np.ndarray            # (n,)  Kosten je Einheit auf CPU
    cost_npu: np.ndarray            # (n,)  Kosten je Einheit auf NPU
    penalty_npu: np.ndarray         # (n,n) Contention beide-auf-NPU (symm., Diag 0)
    penalty_cpu: np.ndarray         # (n,n) Contention beide-auf-CPU (symm., Diag 0)

    def __post_init__(self):
        self.cost_cpu = np.asarray(self.cost_cpu, dtype=np.float64)
        self.cost_npu = np.asarray(self.cost_npu, dtype=np.float64)
        n = self.cost_cpu.shape[0]
        for name in ("penalty_npu", "penalty_cpu"):
            P = np.asarray(getattr(self, name), dtype=np.float64)
            if P.shape != (n, n):
                raise ValueError(f"{name}: erwartet ({n},{n}), bekam {P.shape}")
            if np.linalg.norm(P - P.T) > 1e-9:
                raise ValueError(f"{name} muss symmetrisch sein (Kostenmodell).")
            if np.any(np.abs(np.diag(P)) > 1e-12):
                raise ValueError(f"{name}: Diagonale muss 0 sein (keine Selbst-Contention).")
            setattr(self, name, P)

    @property
    def n(self) -> int:
        return int(self.cost_cpu.shape[0])

    def total_cost(self, x: np.ndarray) -> float:
        """Direkte Auswertung von H(x) — unabhaengiger Rechenweg fuer die
        Verifikation der QUBO-Kodierung (kein Umweg ueber Q)."""
        x = np.asarray(x, dtype=np.float64)
        cost = float(self.cost_npu @ x + self.cost_cpu @ (1.0 - x))
        for i in range(self.n):
            for j in range(i + 1, self.n):
                cost += self.penalty_npu[i, j] * x[i] * x[j]
                cost += self.penalty_cpu[i, j] * (1.0 - x[i]) * (1.0 - x[j])
        return cost


def build_qubo(problem: ScheduleProblem) -> tuple[np.ndarray, float]:
    """Baut das symmetrische Q und den Offset gemaess dem Kodierungs-Satz."""
    n = problem.n
    Q = (problem.penalty_npu + problem.penalty_cpu) / 2.0  # Diagonalen sind 0
    lin = (problem.cost_npu - problem.cost_cpu
           - problem.penalty_cpu.sum(axis=1))              # Zeilensumme, Diag 0
    Q = Q.copy()
    Q[np.arange(n), np.arange(n)] = lin
    offset = float(problem.cost_cpu.sum()
                   + problem.penalty_cpu[np.triu_indices(n, 1)].sum())
    return Q, offset


def greedy_schedule(problem: ScheduleProblem) -> np.ndarray:
    """Supervisor-Heuristik: Einheiten sequenziell auf die Seite mit den
    geringeren Grenzkosten (inkl. Contention gegen bereits Zugewiesene)."""
    n = problem.n
    x = np.zeros(n, dtype=np.int64)
    for i in range(n):
        cost_if_cpu = problem.cost_cpu[i] + sum(
            problem.penalty_cpu[i, j] for j in range(i) if x[j] == 0)
        cost_if_npu = problem.cost_npu[i] + sum(
            problem.penalty_npu[i, j] for j in range(i) if x[j] == 1)
        x[i] = 1 if cost_if_npu < cost_if_cpu else 0
    return x


def solve_schedule(problem: ScheduleProblem, steps: int = 4000,
                   n_restarts: Optional[int] = None,
                   base_seed: int = 0) -> Dict:
    """Loest das Scheduling: SA auf dem QUBO, Greedy als garantierte Basis.

    Rueckgabe enthaelt beide Loesungen; 'assignment' ist die bessere
    (=> nie schlechter als Greedy, by construction)."""
    Q, offset = build_qubo(problem)
    res = parallel_anneal(Q, steps=steps, n_restarts=n_restarts or 4,
                          base_seed=base_seed)
    x_sa = np.asarray(res["solution"], dtype=np.int64)
    cost_sa = float(res["energy"]) + offset
    x_greedy = greedy_schedule(problem)
    cost_greedy = problem.total_cost(x_greedy)

    if cost_sa <= cost_greedy:
        best_x, best_cost, winner = x_sa, cost_sa, "sa"
    else:
        best_x, best_cost, winner = x_greedy, cost_greedy, "greedy"
    return {
        "assignment": best_x,                 # 0 = CPU, 1 = NPU
        "total_cost": best_cost,
        "winner": winner,
        "cost_sa": cost_sa,
        "cost_greedy": cost_greedy,
        "sa_strictly_better": bool(cost_sa < cost_greedy - 1e-9),
        "offset": offset,
        "runtime_seconds": res["runtime_seconds"],
    }


def random_problem(n: int, rng: np.random.Generator,
                   contention_density: float = 0.3) -> ScheduleProblem:
    """Synthetische Instanz fuer Benchmarks/Tests (Kosten in 'ms')."""
    cost_cpu = rng.uniform(1.0, 10.0, n)
    cost_npu = rng.uniform(0.2, 8.0, n)

    def _sym_penalty():
        mask = rng.random((n, n)) < contention_density
        P = np.where(mask, rng.uniform(0.5, 5.0, (n, n)), 0.0)
        P = np.triu(P, 1)
        return P + P.T

    return ScheduleProblem(cost_cpu, cost_npu, _sym_penalty(), _sym_penalty())


if __name__ == "__main__":
    rng = np.random.default_rng(7)
    prob = random_problem(24, rng)
    out = solve_schedule(prob, steps=6000)
    npu_units = int(out["assignment"].sum())
    print(f"n=24 Einheiten -> NPU: {npu_units}, CPU: {24 - npu_units}")
    print(f"Kosten SA: {out['cost_sa']:.3f} | Greedy: {out['cost_greedy']:.3f} "
          f"| Gewinner: {out['winner']} (SA strikt besser: {out['sa_strictly_better']})")
