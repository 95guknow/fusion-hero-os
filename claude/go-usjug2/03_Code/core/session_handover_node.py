# -*- coding: utf-8 -*-
"""
session_handover_node.py — HAUPTKNOTEN: Sitzungs-Übergabe (Handover)
====================================================================
Verbessert Automatisierung ZWISCHEN Sitzungen: erfasst beim Sitzungsende den
offenen Zustand (anstehende Scheduler-Tasks, aktive Fäden, Kontext-Anker) und
erzeugt beim Start der nächsten Sitzung einen RESUME-Plan — damit Abläufe nicht
neu starten, sondern fortgesetzt werden.

Verbindet drei Knoten read-only:
  * automation_scheduler  -> offene (pending/planned) Tasks
  * faden_store           -> aktive Fäden (nach Stärke-Tier)
  * conversation_context  -> Root-Kontext-Anker

Cross-Session: append-only JSON-Log der Handover-Snapshots. Ehrlich: reine
Erfassung + Resume-PLAN (keine Auto-Ausführung; Signale read-only, keine
Schreibzugriffe auf fremde Stores).

Aufruf:  python session_handover_node.py     # Demo: capture -> resume
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


def _state_root() -> Path:
    root = Path(os.getenv("FUSION_STATE_DIR", os.path.expanduser("~/.fusion-hero-os")))
    return root / "session_handover"


@dataclass
class Handover:
    handover_id: str
    session_id: str
    ended_at: float
    open_tasks: List[Dict[str, Any]] = field(default_factory=list)
    active_threads: Dict[str, int] = field(default_factory=dict)   # tier -> count
    context_anchor: str = ""
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _read_open_tasks() -> List[Dict[str, Any]]:
    try:
        from automation_scheduler_node import get_node
        return [{"task_id": t.task_id, "portal": t.portal, "action": t.action,
                 "cost": t.cost, "value": t.value, "status": t.status}
                for t in get_node().pending()]
    except Exception:
        return []


def _read_active_threads() -> Dict[str, int]:
    try:
        from faden_store import get_faden_store
        counts: Dict[str, int] = {}
        for t in get_faden_store()._threads.values():
            counts[t.strength] = counts.get(t.strength, 0) + 1
        return counts
    except Exception:
        return {}


def _read_context_anchor() -> str:
    try:
        from conversation_context_core import get_context
        st = get_context().status()
        root = st.get("root_window") or {}
        return str(root.get("executive_summary") or "")[:200]
    except Exception:
        return ""


class SessionHandoverNode:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = path or (_state_root() / "handover_log.json")
        self.log: List[Handover] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.log = [Handover(**h) for h in data.get("handovers", [])]
        except Exception:
            self.log = []

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"version": "1.0", "updated_at": time.time(),
                                        "handovers": [h.to_dict() for h in self.log[-50:]]},
                                       indent=2, ensure_ascii=False), encoding="utf-8")

    def capture(self, session_id: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Sitzungsende: offenen Zustand erfassen (read-only aus den realen Knoten)."""
        h = Handover(
            handover_id=uuid.uuid4().hex[:12],
            session_id=session_id,
            ended_at=time.time(),
            open_tasks=_read_open_tasks(),
            active_threads=_read_active_threads(),
            context_anchor=_read_context_anchor(),
            meta=meta or {},
        )
        self.log.append(h)
        self._save()
        return h.to_dict()

    def resume(self, new_session_id: str) -> Dict[str, Any]:
        """Sitzungsstart: aus dem letzten Handover einen Resume-Plan erzeugen."""
        if not self.log:
            return {"ok": False, "reason": "kein Handover vorhanden", "session": new_session_id}
        last = self.log[-1]
        # Resume-Plan: offene Tasks nach Wert priorisiert + Faden-/Kontext-Kontinuität
        tasks = sorted(last.open_tasks, key=lambda t: -float(t.get("value", 0)))
        steps: List[str] = []
        if tasks:
            steps.append(f"{len(tasks)} offene Automatisierungs-Tasks fortsetzen "
                         f"(Top: {tasks[0]['action']} @ {tasks[0]['portal']})")
        if last.active_threads:
            strong = sum(v for k, v in last.active_threads.items() if k in ("stark", "fixpunkt"))
            steps.append(f"{sum(last.active_threads.values())} aktive Fäden übernehmen "
                         f"({strong} stark/fixpunkt-nah)")
        if last.context_anchor:
            steps.append("Start-Kontext an letzten Anker anknüpfen")
        return {
            "ok": True,
            "from_session": last.session_id,
            "to_session": new_session_id,
            "gap_s": round(time.time() - last.ended_at, 1),
            "resume_plan": steps,
            "carry_open_tasks": tasks,
            "carry_threads": last.active_threads,
            "context_anchor": last.context_anchor,
        }

    def status(self) -> Dict[str, Any]:
        return {"node": "session_handover", "store": str(self.path),
                "handovers": len(self.log),
                "last": self.log[-1].to_dict() if self.log else None}


_NODE: Optional[SessionHandoverNode] = None


def get_node() -> SessionHandoverNode:
    global _NODE
    if _NODE is None:
        _NODE = SessionHandoverNode()
    return _NODE


# ==================================================================
if __name__ == "__main__":
    import tempfile

    print("=" * 70)
    print("  HAUPTKNOTEN: Sitzungs-Übergabe (Handover)")
    print("=" * 70)

    store = Path(tempfile.gettempdir()) / "session_handover_demo.json"
    if store.exists():
        store.unlink()
    node = SessionHandoverNode(path=store)

    # Sitzung A endet: capture (reale Knoten read-only; im Demo evtl. leer -> ehrlich)
    cap = node.capture("sitzung-A", meta={"grund": "session-end"})
    print(f"\n[CAPTURE sitzung-A] handover_id={cap['handover_id']}")
    print(f"  offene Tasks: {len(cap['open_tasks'])} | aktive Fäden: {cap['active_threads']} "
          f"| Kontext-Anker: {'ja' if cap['context_anchor'] else '(leer)'}")

    # Falls die realen Knoten leer sind: synthetischen Zustand einspielen, um den
    # Resume-Plan sichtbar zu machen (ehrlich als Demo-Fallback markiert).
    if not cap["open_tasks"]:
        node.log[-1].open_tasks = [
            {"task_id": "t1", "portal": "github", "action": "PR-Sync main<-v2-beta", "cost": 8, "value": 9.0, "status": "planned"},
            {"task_id": "t2", "portal": "supabase", "action": "Cloud-Mirror", "cost": 5, "value": 6.0, "status": "pending"},
        ]
        node.log[-1].active_threads = {"stark": 2, "mittel": 5, "fein": 3}
        node.log[-1].context_anchor = "QUBO+Supabase-Arbeit, Faden-Stärke-Coevolution"
        node._save()
        print("  (Demo-Fallback: synthetischer offener Zustand eingespielt)")

    # Sitzung B startet: resume
    plan = node.resume("sitzung-B")
    print(f"\n[RESUME sitzung-B] aus {plan['from_session']}, Lücke {plan['gap_s']}s")
    for i, step in enumerate(plan["resume_plan"], 1):
        print(f"  {i}. {step}")
    print(f"\n  Cross-Session verifiziert: neuer Node lädt {SessionHandoverNode(path=store).status()['handovers']} Handover(s)")
    print("=" * 70)
