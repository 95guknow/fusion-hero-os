# -*- coding: utf-8 -*-
"""
cost_estimator_node.py — HAUPTKNOTEN: Datengetriebener Kosten-Schätzer
======================================================================
Macht die Ressourcenoptimierung des automation_scheduler datengetrieben: statt
handgesetzter Task-Kosten schätzt dieser Knoten die realen Ressourcenkosten je
(Portal, Aktionstyp) aus der beobachteten Historie — per exponentiell
gewichtetem gleitenden Mittel (EWMA).

  * observe(portal, action, actual_cost)  -> Historie/EWMA aktualisieren
  * estimate(portal, action)              -> geschätzte Kosten (int, für Scheduler)
  * Cold-Start-Fallback: ohne Historie ein konservativer Default.

Cross-Session: persistenter JSON-Store der EWMA-Zustände. Ehrlich: bewusst eine
EINFACHE EWMA-Heuristik, KEIN gelerntes/ML-Modell — im Docstring so markiert
(Code-Honesty). Konfidenz steigt mit der Beobachtungszahl (transparent gemeldet).

Aufruf:  python cost_estimator_node.py     # Demo: beobachten -> konvergierende Schätzung
"""
from __future__ import annotations

import json
import math
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

_ALPHA = float(os.getenv("FUSION_COST_EWMA_ALPHA", "0.3"))   # Glättung (0..1; höher = reaktiver)
_DEFAULT_COST = float(os.getenv("FUSION_COST_DEFAULT", "5"))  # Cold-Start-Fallback


def _state_root() -> Path:
    root = Path(os.getenv("FUSION_STATE_DIR", os.path.expanduser("~/.fusion-hero-os")))
    return root / "cost_estimator"


def _key(portal: str, action: str) -> str:
    """Normalisiert (Portal, Aktion) zu einem stabilen Schätz-Schlüssel."""
    words = re.findall(r"[a-zA-Zäöüß0-9]+", (action or "").lower())
    return f"{(portal or 'local').lower()}::{'_'.join(words[:3]) or 'generic'}"


@dataclass
class CostStat:
    key: str
    ewma: float
    count: int = 0
    m2: float = 0.0            # für laufende Varianz (Welford-ähnlich, grob)
    last_ts: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CostEstimatorNode:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or (_state_root() / "cost_stats.json")
        self.stats: Dict[str, CostStat] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            for s in data.get("stats", []):
                self.stats[s["key"]] = CostStat(**s)
        except Exception:
            self.stats = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"version": "1.0", "updated_at": time.time(),
                                        "stats": [s.to_dict() for s in self.stats.values()]},
                                       indent=2, ensure_ascii=False), encoding="utf-8")

    def observe(self, portal: str, action: str, actual_cost: float) -> Dict[str, Any]:
        k = _key(portal, action)
        st = self.stats.get(k)
        c = float(actual_cost)
        if st is None:
            st = CostStat(key=k, ewma=c, count=1, m2=0.0)
        else:
            prev = st.ewma
            st.ewma = (1 - _ALPHA) * st.ewma + _ALPHA * c
            st.count += 1
            st.m2 += (c - prev) * (c - st.ewma)  # grobe laufende Streuung
        st.last_ts = time.time()
        self.stats[k] = st
        self._save()
        return {"key": k, "ewma": round(st.ewma, 3), "count": st.count}

    def estimate(self, portal: str, action: str) -> Dict[str, Any]:
        k = _key(portal, action)
        st = self.stats.get(k)
        if st is None:
            return {"key": k, "cost": max(1, int(round(_DEFAULT_COST))),
                    "ewma": round(float(_DEFAULT_COST), 3), "count": 0, "std": 0.0,
                    "confidence": 0.0, "source": "cold_start_default"}
        confidence = 1.0 - math.exp(-st.count / 5.0)  # steigt mit Beobachtungen, saturiert
        std = math.sqrt(max(0.0, st.m2 / st.count)) if st.count > 1 else 0.0
        return {"key": k, "cost": max(1, int(round(st.ewma))), "ewma": round(st.ewma, 3),
                "count": st.count, "std": round(std, 3), "confidence": round(confidence, 3), "source": "ewma"}

    def status(self) -> Dict[str, Any]:
        return {"node": "cost_estimator", "store": str(self.path), "alpha": _ALPHA,
                "keys": len(self.stats),
                "top": sorted(({"key": s.key, "ewma": round(s.ewma, 2), "count": s.count}
                               for s in self.stats.values()), key=lambda x: -x["count"])[:10]}


_NODE: Optional[CostEstimatorNode] = None


def get_node() -> CostEstimatorNode:
    global _NODE
    if _NODE is None:
        _NODE = CostEstimatorNode()
    return _NODE


# ==================================================================
if __name__ == "__main__":
    import tempfile

    print("=" * 70)
    print("  HAUPTKNOTEN: Datengetriebener Kosten-Schätzer (EWMA)")
    print("=" * 70)

    store = Path(tempfile.gettempdir()) / "cost_estimator_demo.json"
    if store.exists():
        store.unlink()
    node = CostEstimatorNode(path=store)

    # Cold start
    est0 = node.estimate("github", "PR-Sync main")
    print(f"\n[COLD START] github/PR-Sync -> cost={est0['cost']} conf={est0['confidence']} ({est0['source']})")

    # Beobachtungen (reale Kosten schwanken um ~8)
    print("\n[BEOBACHTUNGEN] reale Kosten ~8 (github/PR-Sync):")
    for c in [7, 9, 8, 10, 8, 9]:
        r = node.observe("github", "PR-Sync main<-v2-beta", c)
    est = node.estimate("github", "PR-Sync main branch")
    print(f"  -> Schätzung konvergiert: cost={est['cost']} ewma={est['ewma']} "
          f"count={est['count']} std={est['std']} conf={est['confidence']}")

    # zweites Portal/Aktion
    for c in [40, 45, 38, 42]:
        node.observe("drive", "robocopy Medienserver", c)
    edr = node.estimate("drive", "robocopy Medienserver")  # gleicher Schlüssel wie beobachtet
    print(f"  drive/robocopy -> cost={edr['cost']} ewma={edr['ewma']} conf={edr['confidence']}")

    # Cross-Session
    node2 = CostEstimatorNode(path=store)
    e2 = node2.estimate("github", "PR-Sync anything")
    print(f"\n[CROSS-SESSION] neuer Node kennt Schätzung weiter: github/PR-Sync cost={e2['cost']} "
          f"(count={e2['count']})")
    print(f"[STATUS] keys={node2.status()['keys']}")
    print("=" * 70)
