# -*- coding: utf-8 -*-
"""
portal_rate_budget_node.py — HAUPTKNOTEN: Pro-Portal-Rate-/Ressourcenbudget
===========================================================================
Ergänzt die globale Ressourcenoptimierung des automation_scheduler um
PORTAL-SPEZIFISCHE Grenzen: jedes Portal (github/supabase/drive/local/mcp) hat
ein Rate-/Ressourcenbudget pro Zeitfenster (z.B. API-Quote, Bandbreite). Der
Knoten trackt Verbrauch, berechnet den Portal-Druck (0..1) und liefert:
  * available(portal)  -> Rest-Budget im Fenster  (Constraint für den Scheduler)
  * pressure(portal)   -> 0..1  (0=frei, 1=Limit)
  * emit_pressure(bus) -> emittiert resource_pressure-Quanten für Portale nahe am
                          Limit (speist den entwicklungsquant_bus).

Cross-Session: persistenter JSON-Store; Verbrauch mit Fenster-TTL (gleitendes
Fenster) überlebt Sitzungen. Ehrlich: nur Buchhaltung + Grenzwerte — kein
verstecktes Portal-Verhalten, keine echten API-Calls.

Aufruf:  python portal_rate_budget_node.py     # Demo + Selbstcheck
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

PORTALS = ("github", "supabase", "drive", "local", "mcp")

# Standard-Budgets je Portal: (einheiten_pro_fenster, fenster_sekunden).
# Konservativ; via env FUSION_PORTAL_BUDGET_<PORTAL> überschreibbar.
DEFAULT_LIMITS: Dict[str, Dict[str, float]] = {
    "github":   {"units": 60, "window_s": 3600},   # ~GitHub-API-artig
    "supabase": {"units": 200, "window_s": 3600},
    "drive":    {"units": 40, "window_s": 3600},
    "local":    {"units": 1000, "window_s": 3600},
    "mcp":      {"units": 120, "window_s": 3600},
}
PRESSURE_EMIT_THRESHOLD = float(os.getenv("FUSION_PORTAL_PRESSURE_EMIT", "0.7"))


def _state_root() -> Path:
    root = Path(os.getenv("FUSION_STATE_DIR", os.path.expanduser("~/.fusion-hero-os")))
    return root / "portal_rate_budget"


@dataclass
class Consumption:
    portal: str
    cost: float
    ts: float = field(default_factory=time.time)
    action: str = ""


class PortalRateBudgetNode:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or (_state_root() / "usage.json")
        self.limits: Dict[str, Dict[str, float]] = {p: dict(DEFAULT_LIMITS.get(p, {"units": 100, "window_s": 3600})) for p in PORTALS}
        for p in PORTALS:  # env-Override
            env = os.getenv(f"FUSION_PORTAL_BUDGET_{p.upper()}")
            if env:
                try:
                    self.limits[p]["units"] = float(env)
                except Exception:
                    pass
        self.usage: List[Consumption] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.usage = [Consumption(**u) for u in data.get("usage", [])]
        except Exception:
            self.usage = []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"version": "1.0", "updated_at": time.time(),
                                         "usage": [asdict(u) for u in self.usage]},
                                        indent=2, ensure_ascii=False), encoding="utf-8")

    def _prune(self, now: Optional[float] = None) -> None:
        """Verbrauch außerhalb des größten Fensters verfällt (gleitendes Fenster)."""
        now = now or time.time()
        max_window = max((l["window_s"] for l in self.limits.values()), default=3600)
        self.usage = [u for u in self.usage if now - u.ts <= max_window]

    def consume(self, portal: str, cost: float, action: str = "") -> Dict[str, Any]:
        portal = portal.lower() if portal.lower() in PORTALS else "local"
        self.usage.append(Consumption(portal=portal, cost=float(cost), action=action))
        self._prune()
        self._save()
        return {"portal": portal, "consumed_now": self.consumed(portal), "available": self.available(portal)}

    def consumed(self, portal: str, now: Optional[float] = None) -> float:
        now = now or time.time()
        win = self.limits[portal]["window_s"]
        return sum(u.cost for u in self.usage if u.portal == portal and now - u.ts <= win)

    def available(self, portal: str) -> float:
        return max(0.0, self.limits[portal]["units"] - self.consumed(portal))

    def pressure(self, portal: str) -> float:
        units = self.limits[portal]["units"] or 1.0
        return min(1.0, self.consumed(portal) / units)

    def caps(self) -> Dict[str, float]:
        """Rest-Budget je Portal — als Constraint für den Scheduler nutzbar."""
        return {p: self.available(p) for p in PORTALS}

    def emit_pressure(self, bus, threshold: float = PRESSURE_EMIT_THRESHOLD, base_magnitude: float = 8.0) -> List[str]:
        """Emittiert resource_pressure-Quanten für Portale >= threshold (speist den Bus)."""
        fired: List[str] = []
        for p in PORTALS:
            pr = self.pressure(p)
            if pr >= threshold:
                bus.emit("portal_rate_budget", "*", "resource_pressure",
                         magnitude=base_magnitude * pr, layer=3, payload={"portal": p, "pressure": round(pr, 3)})
                fired.append(p)
        return fired

    def status(self) -> Dict[str, Any]:
        self._prune()
        return {
            "node": "portal_rate_budget",
            "store": str(self.path),
            "by_portal": {p: {"limit": self.limits[p]["units"], "consumed": round(self.consumed(p), 2),
                              "available": round(self.available(p), 2), "pressure": round(self.pressure(p), 3)}
                          for p in PORTALS},
        }


_NODE: Optional[PortalRateBudgetNode] = None


def get_node() -> PortalRateBudgetNode:
    global _NODE
    if _NODE is None:
        _NODE = PortalRateBudgetNode()
    return _NODE


# ==================================================================
if __name__ == "__main__":
    import tempfile

    print("=" * 70)
    print("  HAUPTKNOTEN: Pro-Portal-Rate-/Ressourcenbudget")
    print("=" * 70)

    store = Path(tempfile.gettempdir()) / "portal_rate_budget_demo.json"
    if store.exists():
        store.unlink()
    node = PortalRateBudgetNode(path=store)

    # Verbrauch simulieren: github stark, supabase moderat
    for _ in range(9):
        node.consume("github", 5, "PR-Sync")     # 45 von 60
    node.consume("supabase", 40, "Cloud-Mirror")  # 40 von 200
    node.consume("drive", 35, "robocopy")          # 35 von 40 -> hoher Druck

    print("\n[STATUS je Portal]")
    for p, v in node.status()["by_portal"].items():
        bar = "#" * int(v["pressure"] * 20)
        print(f"  {p:8} limit={v['limit']:>5} consumed={v['consumed']:>6} avail={v['available']:>6} "
              f"druck={v['pressure']:.2f} {bar}")

    print(f"\n[CAPS für Scheduler] {json.dumps(node.caps(), ensure_ascii=False)}")

    # Bus-Integration: Portale nahe am Limit emittieren resource_pressure
    from entwicklungsquant_bus import EntwicklungsquantBus
    bus = EntwicklungsquantBus()
    bus.register("automation_scheduler", [("resource_pressure", "plan_change", "conversation_context", 0.4)])
    bus.register("conversation_context")
    fired = node.emit_pressure(bus, threshold=0.7)
    res = bus.run_until_fixpoint()
    print(f"\n[BUS] Portale über Druck-Schwelle 0.7 -> resource_pressure emittiert: {fired}")
    print(f"      Ko-Entwicklung: Fixpunkt={res['fixpunkt_erreicht']} in {res['ticks']} Ticks, "
          f"Quanten={res['quanten_total']}")

    # Cross-Session: neuer Node lädt denselben Store
    node2 = PortalRateBudgetNode(path=store)
    print(f"\n[CROSS-SESSION] neuer Node lädt Verbrauch: github consumed="
          f"{node2.consumed('github')} (erwartet 45)")
    print("=" * 70)
