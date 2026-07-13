# -*- coding: utf-8 -*-
"""
automation_scheduler_node.py — HAUPTKNOTEN: Ressourcenoptimierter Automatisierungs-Scheduler
============================================================================================
Verbessert Automatisierungen in den Abläufen ZWISCHEN Sitzungen und über
verschiedene PORTALE hinweg, indem er unter einem Ressourcenbudget die
wertmaximale Teilmenge anstehender Automatisierungs-Tasks auswählt.

Einordnung im System (dockt an Vorhandenes an, ersetzt nichts):
  * Cross-Session : persistenter JSON-Store im State-Dir (wie faden_store /
                    fusion_profile) -> Tasks überleben Sitzungen und werden fortgesetzt.
  * Cross-Portal  : jeder Task ist einem Portal zugeordnet (github/supabase/
                    drive/local/mcp); optionale Pro-Portal-Kappen.
  * Ressourcen-Opt: Budget aus fusion_profile (max_parallel_agents × Ratio);
                    Auswahl = 0/1-Knapsack (Wert maximieren, Kosten ≤ Budget).
                    Primär EXAKT (DP, garantiert optimal, für diese Größen billig).
                    Zusätzlich QUBO-Pfad (qb_qubo) — gegen die exakte Lösung
                    VERIFIZIERT, NICHT als überlegen behauptet (QUBO-SCHEDULER-
                    NUTZEN ist in proof_registry.yaml bewusst OFFEN).

Code-Honesty:
  * Der Knoten PLANT/priorisiert. Ausführung ist per Default DRY-RUN — es werden
    KEINE echten Portal-Aktionen ausgelöst (konsistent mit der dry-run-Default-
    Policy der Connectoren). Reale Ausführung nur mit explizitem executor + Flag.
  * Kosten sind ganzzahlige Ressourceneinheiten (klare DP-/QUBO-Kodierung).

Aufruf:  python automation_scheduler_node.py     # Demo + Selbstverifikation
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

PORTALS = ("github", "supabase", "drive", "local", "mcp")
VALID_STATUS = ("pending", "planned", "done", "skipped")


def _state_root() -> Path:
    root = Path(os.getenv("FUSION_STATE_DIR", os.path.expanduser("~/.fusion-hero-os")))
    return root / "automation_scheduler"


def _store_path() -> Path:
    return _state_root() / "tasks.json"


# --------------------------------------------------------------------------- #
#  Ressourcenbudget aus fusion_profile (mit Fallback)                          #
# --------------------------------------------------------------------------- #
def resource_budget(default: int = 100) -> Dict[str, Any]:
    """Abstraktes Ressourcenbudget (Einheiten) aus dem aktiven fusion_profile."""
    try:
        import sys
        dash = Path(__file__).resolve().parents[1] / "Dashboard"
        if str(dash) not in sys.path:
            sys.path.insert(0, str(dash))
        from fusion_profile import get_profile_config

        cfg = get_profile_config()
        agents = int(cfg.get("max_parallel_agents", 4))
        ratio = float(cfg.get("worker_cap_ratio", 0.75))
        units = max(10, int(round(agents * 20 * ratio)))
        return {"budget": units, "profile": cfg.get("id", "?"), "source": "fusion_profile"}
    except Exception:
        env = os.getenv("FUSION_AUTOMATION_BUDGET")
        return {"budget": int(env) if env else default, "profile": None, "source": "fallback"}


# --------------------------------------------------------------------------- #
#  Task-Modell                                                                #
# --------------------------------------------------------------------------- #
@dataclass
class AutomationTask:
    task_id: str
    portal: str                       # github | supabase | drive | local | mcp
    action: str                       # menschenlesbares Label des Ablaufs
    cost: int = 1                     # Ressourceneinheiten (int)
    value: float = 1.0                # Nutzen/Priorität
    status: str = "pending"
    dry_run: bool = True
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    last_session: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "AutomationTask":
        portal = (raw.get("portal") or "local").lower()
        if portal not in PORTALS:
            portal = "local"
        status = raw.get("status") if raw.get("status") in VALID_STATUS else "pending"
        return cls(
            task_id=str(raw.get("task_id") or uuid.uuid4().hex[:12]),
            portal=portal,
            action=str(raw.get("action") or ""),
            cost=max(1, int(raw.get("cost") or 1)),
            value=float(raw.get("value") or 1.0),
            status=status,
            dry_run=bool(raw.get("dry_run", True)),
            created_at=float(raw.get("created_at") or time.time()),
            updated_at=float(raw.get("updated_at") or time.time()),
            last_session=str(raw.get("last_session") or ""),
            meta=dict(raw.get("meta") or {}),
        )


# --------------------------------------------------------------------------- #
#  Ressourcenoptimierung: exakter Knapsack (DP) + QUBO-Pfad (verifiziert)      #
# --------------------------------------------------------------------------- #
def knapsack_exact(costs: List[int], values: List[float], budget: int) -> Tuple[List[int], float]:
    """0/1-Knapsack (garantiert optimal). Gibt (gewählte Indizes, Gesamtwert)."""
    n = len(costs)
    if n == 0 or budget <= 0:
        return [], 0.0
    # dp[c] = bester Wert mit Kapazität c; keep[i][c] für Rekonstruktion
    dp = [0.0] * (budget + 1)
    keep = [[False] * (budget + 1) for _ in range(n)]
    for i in range(n):
        ci, vi = costs[i], values[i]
        for c in range(budget, ci - 1, -1):
            if dp[c - ci] + vi > dp[c]:
                dp[c] = dp[c - ci] + vi
                keep[i][c] = True
    chosen: List[int] = []
    c = budget
    for i in range(n - 1, -1, -1):
        if keep[i][c]:
            chosen.append(i)
            c -= costs[i]
    chosen.reverse()
    return chosen, dp[budget]


def _knapsack_qubo_matrix(costs: List[int], values: List[float], budget: int):
    """Kodiert das Knapsack als QUBO (numpy Q). Vars: n Tasks + Slack-Bits.

    H = -A·Σ v_i x_i + P·(Budget - Σ c_i x_i - Σ 2^k s_k)^2
    (Slack-Bits verwandeln 'Kosten ≤ Budget' in eine Gleichung.)
    """
    import numpy as np

    n = len(costs)
    slack_bits = max(1, int(budget).bit_length())
    a = [float(c) for c in costs] + [float(1 << k) for k in range(slack_bits)]
    m = n + slack_bits
    A = 1.0
    # P nur so groß wie nötig: verhindert Budget-Überschreitung (P > max marginaler
    # Wertgewinn), ohne den Wert-Gradienten zu überdämpfen (sonst findet SA nur
    # feasible-aber-suboptimal). Zu großes P = flacher Wert-Kontrast.
    P = A * (max(values) * 1.6 + 1.0) if values else 1.0

    Q = np.zeros((m, m), dtype=np.float64)
    for j in range(m):
        # Diagonale: Wertterm (nur Tasks) + Penalty-Diagonalanteil
        val_term = -A * values[j] if j < n else 0.0
        Q[j, j] = val_term + P * (a[j] * a[j] - 2.0 * budget * a[j])
    for j in range(m):
        for l in range(j + 1, m):
            Q[j, l] = Q[l, j] = P * a[j] * a[l]
    return Q, n


def _import_qb_qubo():
    import sys
    here = Path(__file__).resolve()
    for rel in ("02_Mathematik", "03_Code/tools", "."):
        p = (here.parents[2] / rel) if rel != "." else here.parents[2]
        if p.exists() and str(p) not in sys.path:
            sys.path.insert(0, str(p))
    import qb_qubo  # noqa
    return qb_qubo


def knapsack_qubo(costs: List[int], values: List[float], budget: int,
                  restarts: int = 16) -> Tuple[List[int], float, bool]:
    """QUBO-Pfad via qb_qubo (SA, mehrere Restarts). Gibt (Indizes, Wert, feasible)."""
    qb = _import_qb_qubo()
    Q, n = _knapsack_qubo_matrix(costs, values, budget)
    best_sel: List[int] = []
    best_val = -1.0
    best_feasible = False
    for _ in range(restarts):
        x, _e = qb.simulated_annealing(Q, steps=8000)
        sel = [i for i in range(n) if int(x[i]) == 1]
        tot_cost = sum(costs[i] for i in sel)
        tot_val = sum(values[i] for i in sel)
        feasible = tot_cost <= budget
        # bevorzuge feasible Lösungen mit höchstem Wert
        if (feasible and not best_feasible) or (feasible == best_feasible and tot_val > best_val):
            best_sel, best_val, best_feasible = sel, tot_val, feasible
    return best_sel, (best_val if best_feasible else 0.0), best_feasible


# --------------------------------------------------------------------------- #
#  Der Hauptknoten                                                            #
# --------------------------------------------------------------------------- #
class AutomationSchedulerNode:
    def __init__(self, path: Optional[Path] = None, session_id: Optional[str] = None) -> None:
        self.path = path or _store_path()
        self.session_id = session_id or os.getenv("FUSION_SESSION_ID", uuid.uuid4().hex[:8])
        self.tasks: Dict[str, AutomationTask] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for raw in data.get("tasks", []):
                t = AutomationTask.from_dict(raw)
                self.tasks[t.task_id] = t
        except Exception:
            self.tasks = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"version": "1.0", "updated_at": time.time(),
                   "tasks": [t.to_dict() for t in self.tasks.values()]}
        self.path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    def add_task(self, portal: str, action: str, cost: int = 1, value: float = 1.0,
                 meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        t = AutomationTask(
            task_id=uuid.uuid4().hex[:12],
            portal=(portal or "local").lower() if (portal or "local").lower() in PORTALS else "local",
            action=action, cost=max(1, int(cost)), value=float(value),
            last_session=self.session_id, meta=meta or {},
        )
        self.tasks[t.task_id] = t
        self._save()
        return t.to_dict()

    def pending(self) -> List[AutomationTask]:
        return [t for t in self.tasks.values() if t.status in ("pending", "planned")]

    def plan(self, budget: Optional[int] = None, verify_qubo: bool = False) -> Dict[str, Any]:
        """Ressourcenoptimierte Auswahl (exakt). Optional QUBO-Verifikation."""
        b = int(budget) if budget is not None else int(resource_budget()["budget"])
        tasks = sorted(self.pending(), key=lambda t: (-t.value, t.cost))
        costs = [t.cost for t in tasks]
        values = [t.value for t in tasks]
        idx, total_value = knapsack_exact(costs, values, b)
        chosen = [tasks[i] for i in idx]
        for t in chosen:
            t.status = "planned"
            t.updated_at = time.time()
            t.last_session = self.session_id
        self._save()

        result: Dict[str, Any] = {
            "budget": b,
            "selected": [{"task_id": t.task_id, "portal": t.portal, "action": t.action,
                          "cost": t.cost, "value": t.value} for t in chosen],
            "total_value": round(total_value, 4),
            "total_cost": sum(t.cost for t in chosen),
            "n_pending": len(tasks),
            "by_portal": {p: sum(1 for t in chosen if t.portal == p) for p in PORTALS if any(t.portal == p for t in chosen)},
            "session": self.session_id,
        }
        if verify_qubo and tasks:
            try:
                q_idx, q_val, feasible = knapsack_qubo(costs, values, b)
                result["qubo"] = {
                    "feasible": feasible, "qubo_value": round(q_val, 4),
                    "matches_exact": feasible and abs(q_val - total_value) < 1e-6,
                    "note": "QUBO gegen exakt verifiziert (nicht als besser behauptet)",
                }
            except Exception as exc:
                result["qubo"] = {"error": str(exc)[:120]}
        return result

    def execute(self, executor: Optional[Callable[[AutomationTask], Dict[str, Any]]] = None,
                dry_run: bool = True) -> Dict[str, Any]:
        """Führt geplante Tasks aus. DRY-RUN per Default: keine echten Portal-Aktionen."""
        planned = [t for t in self.tasks.values() if t.status == "planned"]
        results = []
        for t in planned:
            if dry_run or executor is None:
                results.append({"task_id": t.task_id, "portal": t.portal, "action": t.action, "dry_run": True})
            else:
                try:
                    res = executor(t)
                    t.status = "done"; t.updated_at = time.time()
                    results.append({"task_id": t.task_id, "portal": t.portal, "result": res, "dry_run": False})
                except Exception as exc:
                    results.append({"task_id": t.task_id, "error": str(exc)[:120]})
        self._save()
        return {"executed": len(results), "dry_run": dry_run or executor is None, "results": results}

    def status(self) -> Dict[str, Any]:
        by_status = {s: sum(1 for t in self.tasks.values() if t.status == s) for s in VALID_STATUS}
        by_portal = {p: sum(1 for t in self.tasks.values() if t.portal == p) for p in PORTALS}
        return {
            "node": "automation_scheduler",
            "session": self.session_id,
            "store": str(self.path),
            "total_tasks": len(self.tasks),
            "by_status": by_status,
            "by_portal": by_portal,
            "resource_budget": resource_budget(),
        }


_NODE: Optional[AutomationSchedulerNode] = None


def get_node() -> AutomationSchedulerNode:
    global _NODE
    if _NODE is None:
        _NODE = AutomationSchedulerNode()
    return _NODE


# ==================================================================
if __name__ == "__main__":
    import tempfile

    print("=" * 72)
    print("  HAUPTKNOTEN: Ressourcenoptimierter Automatisierungs-Scheduler")
    print("=" * 72)

    # isolierter Store (keine echten Sitzungsdaten berühren)
    store = Path(tempfile.gettempdir()) / "automation_scheduler_demo.json"
    if store.exists():
        store.unlink()
    node = AutomationSchedulerNode(path=store, session_id="demo-A")

    # Cross-Portal Automatisierungs-Tasks
    node.add_task("github", "PR-Sync main<-v2-beta", cost=8, value=9.0)
    node.add_task("supabase", "fusion_events -> Cloud spiegeln", cost=5, value=6.0)
    node.add_task("drive", "Medienserver robocopy", cost=12, value=4.0)
    node.add_task("mcp", "Supabase-Tabellen-Check", cost=2, value=3.0)
    node.add_task("local", "qb_qubo-Kopien byte-sync", cost=3, value=7.0)
    node.add_task("github", "Organigramm-PDF rendern", cost=6, value=2.0)
    node.add_task("supabase", "Settings-Cloud upsert", cost=4, value=5.0)

    print(f"\nRessourcenbudget: {resource_budget()}")
    plan = node.plan(budget=20, verify_qubo=True)
    print(f"\n[PLAN] Budget={plan['budget']}  Kosten={plan['total_cost']}  Wert={plan['total_value']}")
    print(f"       n_pending={plan['n_pending']}  Portale={plan['by_portal']}")
    for s in plan["selected"]:
        print(f"   ✓ [{s['portal']:8}] {s['action']:32} cost={s['cost']} value={s['value']}")
    print(f"\n[QUBO-Verifikation] {plan.get('qubo')}")

    # Dry-run Ausführung (keine echten Portal-Aktionen)
    ex = node.execute(dry_run=True)
    print(f"\n[EXECUTE dry-run] {ex['executed']} Tasks geplant-ausgeführt (dry_run={ex['dry_run']})")

    # Cross-Session: neue Sitzung lädt denselben Store und setzt fort
    node2 = AutomationSchedulerNode(path=store, session_id="demo-B")
    print(f"\n[CROSS-SESSION] Sitzung 'demo-B' lädt Store: {node2.status()['total_tasks']} Tasks, "
          f"Status={node2.status()['by_status']}")

    # kleine Batterie: QUBO == exakt auf Zufallsinstanzen (ehrliche Trefferquote)
    import numpy as np
    rng = np.random.default_rng(7)
    match = 0
    trials = 6
    for _ in range(trials):
        k = int(rng.integers(4, 8))
        cs = [int(rng.integers(1, 8)) for _ in range(k)]
        vs = [float(rng.integers(1, 10)) for _ in range(k)]
        bud = int(sum(cs) * 0.6)
        _, exact_v = knapsack_exact(cs, vs, bud)
        _, q_v, feas = knapsack_qubo(cs, vs, bud)
        if feas and abs(q_v - exact_v) < 1e-6:
            match += 1
    print(f"\n[QUBO vs. EXAKT] {match}/{trials} Instanzen exakt getroffen "
          f"(ehrlich: SA-Heuristik, nicht garantiert optimal)")
    print("=" * 72)
