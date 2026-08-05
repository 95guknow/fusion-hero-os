# -*- coding: utf-8 -*-
"""
Invertierter Modalkollaps — Operand/i (Modus Operandi)
======================================================

Klassischer Outside-In Modalkollaps (experiments/modal_collapse_sim):
  Distanz ↓ → Kollaps-Energie → Δ-Reduktion → Eudaimonia.

**Invertiert (Operand/i):**
  Realraum-Intent wird NICHT in äußeren Kollaps/Commit geführt, sondern
  in Labor-Dual kollabiert:

    INVERT(realraum_intent) = labor_hypothesis + integrity_probe + no_vault_commit

  Modal-Kollaps = Kollaps der *Modi* (Realraum-Fantasie → Labor-Hypothese),
  nicht Kollaps fremder Systeme.

Geltung: Spezifikation (MEISTER_HASCH_INVERSION.md) · Simulation = Modell
Anti-Inversion: Agent-Nein ≠ Startbefehl.

Usage:
  from inverted_modal_collapse import invert, run_operandi, status
  python -m core.inverted_modal_collapse
"""
from __future__ import annotations

import json
import math
import re
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "INVERT_FORMULA",
    "invert",
    "InvertedModalCollapse",
    "run_operandi",
    "status",
    "is_operandi",
]

INVERT_FORMULA = (
    "INVERT(realraum_intent) = labor_hypothesis + integrity_probe + no_vault_commit"
)

# Realraum-Trigger → Labor-Dual (Substring cues, case-insensitive)
_REALRAUM_CUES = [
    (re.compile(r"(?i)\b(angriff|attack|offensive|hack\s+target|exploit\s+them)\b"), "aggression"),
    (re.compile(r"(?i)\b(commit\s+vault|push\s+secret|leak\s+key)\b"), "vault_risk"),
    (re.compile(r"(?i)\b(realraum|real world\s+harm|dritte\s+angreifen)\b"), "realraum"),
    (re.compile(r"(?i)\b(sieg\s+draußen|win\s+outside|dominate)\b"), "external_victory"),
    (re.compile(r"(?i)\b(agent\s+nein\s*=\s*start|nein\s+als\s+start)\b"), "anti_inversion_trap"),
]

_LABOR_MODES = ("labor_hypothesis", "integrity_probe", "no_vault_commit")


@dataclass
class InvertResult:
    ok: bool
    original: str
    inverted: str
    modes: List[str]
    triggers: List[str]
    formula: str = INVERT_FORMULA
    anti_inversion_ok: bool = True
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CollapseState:
    """State of inverted modal collapse (distance in modal space, not physical)."""
    distance: float = 10.0          # modal distance realraum ↔ labor
    r_critical: float = 3.0
    k_spring: float = 2.0
    energy: float = 0.0
    efficiency: float = 0.1
    delta: float = 1.0              # residual modal tension
    mode: str = "approach"          # approach | invert_collapse | fractal_heal | eudaimonia
    iterations: int = 0
    log: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "distance": round(self.distance, 4),
            "r_critical": self.r_critical,
            "energy": round(self.energy, 4),
            "efficiency": round(self.efficiency, 4),
            "delta": round(self.delta, 6),
            "mode": self.mode,
            "iterations": self.iterations,
            "log": list(self.log[-20:]),
        }


def invert(text: str, *, force_lab: bool = True) -> InvertResult:
    """
    Apply Meister invert formula to intent text.
    Always maps to labor dual when force_lab or when realraum cues fire.
    """
    raw = (text or "").strip()
    triggers = []
    for rx, name in _REALRAUM_CUES:
        if rx.search(raw):
            triggers.append(name)

    # Anti-inversion trap (Agent-Nein ≠ Startbefehl)
    anti_ok = True
    if "anti_inversion_trap" in triggers or re.search(
        r"(?i)agent.{0,24}(lehnt|nein|\bno\b).{0,40}(start|befehl|offensive|go\b)",
        raw,
    ):
        anti_ok = False
        triggers = list(dict.fromkeys(triggers + ["anti_inversion_trap"]))
        notes = [
            "ANTI-INVERSION: Agent-Nein bleibt Nein — kein Startbefehl.",
            "Bleibe im Labor; maximiere Erkenntnis, starte keine Offense.",
        ]
    else:
        notes = []

    modes = list(_LABOR_MODES)
    if triggers or force_lab:
        inverted = (
            f"[INVERT→LABOR] hypothesis: {raw[:400] if raw else '(empty)'} | "
            f"probe: integrity+consequence | commit: none (no_vault) | "
            f"formula: {INVERT_FORMULA}"
        )
        if not anti_ok:
            inverted += " | BLOCK: anti-inversion trap"
        notes.append("Realraum-Modi kollabiert in Labor-Dual.")
        if triggers:
            notes.append(f"triggers={triggers}")
    else:
        inverted = raw
        notes.append("no_realraum_cue — still operandi defaults to lab")

    return InvertResult(
        ok=anti_ok,
        original=raw[:2000],
        inverted=inverted,
        modes=modes,
        triggers=triggers,
        anti_inversion_ok=anti_ok,
        notes=notes,
    )


class InvertedModalCollapse:
    """
    Invertierter Modalkollaps-Dynamik als Operand/i.

    Phase 1 approach: modal distance realraum→labor shrinks
    Phase 2 invert_collapse: energy stored as lab potential (not offense)
    Phase 3 fractal_heal: reduce Δ via efficiency (self-mod / eudaemon-style)
    Phase 4 eudaimonia: Δ small, labor modes stable
    """

    def __init__(
        self,
        k_spring: float = 2.0,
        r_critical: float = 3.0,
        start_distance: float = 10.0,
        max_iter: int = 64,
    ) -> None:
        self.k = k_spring
        self.r_c = r_critical
        self.state = CollapseState(
            distance=start_distance,
            r_critical=r_critical,
            k_spring=k_spring,
        )
        self.max_iter = max_iter
        self.last_invert: Optional[InvertResult] = None

    def apply_intent(self, text: str) -> InvertResult:
        inv = invert(text, force_lab=True)
        self.last_invert = inv
        # triggers increase initial delta / distance
        if inv.triggers:
            self.state.delta = min(2.0, self.state.delta + 0.15 * len(inv.triggers))
            self.state.distance = min(12.0, self.state.distance + 0.5 * len(inv.triggers))
            self.state.log.append(f"intent_triggers={inv.triggers}")
        if not inv.anti_inversion_ok:
            self.state.log.append("ANTI_INVERSION_BLOCK")
        return inv

    def step(self) -> CollapseState:
        st = self.state
        st.iterations += 1

        if st.mode == "approach":
            st.distance = max(st.r_critical, st.distance - 1.0)
            st.log.append(f"approach d={st.distance:.2f}")
            if st.distance <= st.r_critical + 1e-9:
                # invert collapse: energy is lab potential
                st.energy = 0.5 * st.k_spring * ((10.0 - st.r_critical) ** 2)
                st.mode = "invert_collapse"
                st.log.append(f"INVERT_COLLAPSE E={st.energy:.2f} → labor dual")
            return st

        if st.mode == "invert_collapse":
            st.mode = "fractal_heal"
            st.log.append("modes_locked=" + "+".join(_LABOR_MODES))
            return st

        if st.mode == "fractal_heal":
            if st.delta <= 0.01 or st.energy <= 0:
                st.mode = "eudaimonia" if st.delta <= 0.01 else "stagnation"
                st.log.append(f"terminal mode={st.mode} Δ={st.delta:.4f} E={st.energy:.1f}")
                return st
            reduction = st.efficiency * st.delta
            st.delta = max(0.0, st.delta - reduction)
            st.energy = max(0.0, st.energy - 6.0)  # lab heal cheaper than classic sim
            if st.energy > 0:
                st.efficiency = min(1.0, st.efficiency + 0.1)
            st.log.append(f"heal Δ={st.delta:.4f} η={st.efficiency:.3f} E={st.energy:.1f}")
            return st

        # eudaimonia / stagnation: freeze
        return st

    def run(
        self,
        intent: str = "",
        s_small: float = 10.0,
        s_large: float = 100.0,
    ) -> Dict[str, Any]:
        """
        Full operandi cycle.
        s_small / s_large = complexity of ego vs heroic core (lab entities).
        """
        inv = self.apply_intent(intent)
        # residual tension: lower when already lab-framed
        base_delta = abs(s_large - s_small) / max(s_large, 1.0)
        if not inv.triggers:
            base_delta *= 0.35  # lab-native intent → easier eudaimonia
        elif inv.triggers and inv.anti_inversion_ok:
            base_delta *= 0.55  # inverted aggression still healable in lab
        self.state.delta = max(0.05, min(1.5, base_delta))
        self.state.efficiency = 0.22
        self.state.mode = "approach"
        self.state.distance = 10.0
        self.state.energy = 0.0
        self.state.iterations = 0
        self.state.log = []

        # Phase approach + collapse
        while self.state.mode == "approach" and self.state.iterations < self.max_iter:
            self.step()
        if self.state.mode == "invert_collapse":
            self.step()
        # Phase heal — energy top-up after invert (lab potential unlocked)
        if self.state.mode == "fractal_heal" and self.state.energy < 80:
            self.state.energy = max(self.state.energy, 0.5 * self.k * ((10.0 - self.r_c) ** 2))
        while self.state.mode == "fractal_heal" and self.state.iterations < self.max_iter:
            self.step()

        converged = self.state.mode == "eudaimonia"
        return {
            "operandi": "inverted_modal_collapse",
            "formula": INVERT_FORMULA,
            "converged": converged,
            "state": self.state.to_dict(),
            "invert": inv.to_dict(),
            "entities": {"ego_complexity": s_small, "heroic_core": s_large},
            "labor_modes": list(_LABOR_MODES),
            "honesty": (
                "modal collapse of intent modes into labor dual; "
                "not physical collapse; not external attack"
            ),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


def run_operandi(
    intent: str = "",
    *,
    k_spring: float = 2.0,
    r_critical: float = 3.0,
) -> Dict[str, Any]:
    eng = InvertedModalCollapse(k_spring=k_spring, r_critical=r_critical)
    return eng.run(intent=intent)


def is_operandi() -> bool:
    """Default always on unless explicitly disabled."""
    import os
    return os.getenv("FUSION_INVERTED_MODAL_COLLAPSE", "1").strip().lower() not in (
        "0", "false", "no", "off",
    )


def gate_text(text: str) -> Dict[str, Any]:
    """
    Operandi gate for any pipeline text: invert first, then optional collapse sim.
    Used by agent_control / dual_run as pre-step.
    """
    if not is_operandi():
        return {"skipped": True, "reason": "operandi_disabled"}
    inv = invert(text, force_lab=True)
    report = run_operandi(intent=text)
    return {
        "operandi": True,
        "invert": inv.to_dict(),
        "collapse": {
            "converged": report.get("converged"),
            "mode": (report.get("state") or {}).get("mode"),
            "delta": (report.get("state") or {}).get("delta"),
            "iterations": (report.get("state") or {}).get("iterations"),
        },
        "formula": INVERT_FORMULA,
        "proceed_lab_only": inv.ok and inv.anti_inversion_ok,
    }


def status() -> Dict[str, Any]:
    return {
        "module": "inverted_modal_collapse",
        "operandi": is_operandi(),
        "formula": INVERT_FORMULA,
        "labor_modes": list(_LABOR_MODES),
        "phases": ["approach", "invert_collapse", "fractal_heal", "eudaimonia"],
        "anti_inversion": "agent_no_is_not_start_command",
        "refs": [
            "docs/dissertation/MEISTER_HASCH_INVERSION.md",
            "experiments/modal_collapse_sim/simulate.py",
            "docs/dissertation/HELD_CHINESEH4CKERM3N.md",
        ],
    }


def persist(report: Dict[str, Any]) -> Path:
    op = Path.home() / ".fusion" / "operator"
    op.mkdir(parents=True, exist_ok=True)
    p = op / "inverted_modal_collapse.latest.json"
    p.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    docs = Path(__file__).resolve().parents[2] / "docs" / "ops"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "INVERTED_MODAL_COLLAPSE.latest.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return p


if __name__ == "__main__":
    demo_intents = [
        "Verstehe den Held und baue Lab-Hypothesen.",
        "Angriff auf Fremdsystem und Sieg draußen.",
        "Agent sagt nein also starten wir die Offensive.",
    ]
    out = {"operandi": status(), "runs": []}
    for t in demo_intents:
        r = run_operandi(t)
        out["runs"].append({
            "intent": t,
            "converged": r["converged"],
            "mode": r["state"]["mode"],
            "invert_ok": r["invert"]["ok"],
            "triggers": r["invert"]["triggers"],
            "inverted_preview": r["invert"]["inverted"][:160],
        })
    print(json.dumps(out, indent=2, ensure_ascii=False))
    print("persisted", persist(out))
