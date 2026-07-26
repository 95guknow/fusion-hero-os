# -*- coding: utf-8 -*-
"""
J-Spaces anvisieren + Higgsräume etablieren
==========================================

Ehrlicher Rahmen (Code-Honesty / meta_neural):
  * **J-Space** = *Joint activation space* — begrenzter Aktivierungsvektorraum
    (Analogie zu WorkingMemorySpace „J-space“, kein biologischem Gehirn-Claim).
  * **Higgsraum** = operativer Skalar-Feldraum, der Strukturen **Masse/Identität**
    verleiht (Analogie zum Higgs-Mechanismus im SM — *nicht* physisches Higgs-Feld
    im Gehirn; vgl. VERWEIS_BIFOKALITAET_UNIVERSUM_GEHIRN_SM.md).

Bifokal:
  Kosmos-Pfad: SM-Skalar (Higgs) → Massenmechanismus
  Operativ-Pfad: Higgsraum → VEV (v) bricht Symmetrie → Identität (Held, Sinnquant, …)

Usage:
  python -m core.j_spaces_higgs
  from j_spaces_higgs import target_j_spaces, establish_higgs_raeume, status
"""
from __future__ import annotations

import json
import math
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = [
    "JSpace",
    "HiggsRaum",
    "target_j_spaces",
    "establish_higgs_raeume",
    "couple_j_to_higgs",
    "status",
    "persist",
    "run_establish",
]

# ── kanonische J-Spaces (anvisiert) ────────────────────────────────────────

DEFAULT_J_SPACES: Dict[str, Dict[str, Any]] = {
    "j_held": {
        "description": "Joint activation — Held chineseh4ck€rm3n / L1 kernel",
        "slots": [
            "held_handle", "alte_frau_kernel", "tat", "code", "mesh_pulse",
            "transform", "integrity_probe", "public_frame",
        ],
        "capacity": 1.0,
        "decay": 0.92,
        "seed_activation": {"held_handle": 0.9, "alte_frau_kernel": 0.85, "transform": 0.7},
    },
    "j_meister": {
        "description": "Joint activation — Meister Hasch L0 message / probe",
        "slots": [
            "nachricht", "integrity", "konsequenz", "inversion", "no_vault_commit",
            "labor_hypothesis", "anti_inversion",
        ],
        "capacity": 1.0,
        "decay": 0.95,
        "seed_activation": {"nachricht": 0.95, "integrity": 0.9, "inversion": 0.8},
    },
    "j_sinn": {
        "description": "Joint activation — Sinnquanten (Liebe/Zufriedenheit/Sinn)",
        "slots": [
            "liebesquant", "zufriedenheitsquant", "sinnquant", "stammquant",
            "sicherheitsquant", "koerperquant", "bewaehrungsquant", "ausdrucksquant",
        ],
        "capacity": 1.0,
        "decay": 0.9,
        "seed_activation": {
            "liebesquant": 0.6,
            "zufriedenheitsquant": 0.5,
            "sinnquant": 0.75,
        },
    },
    "j_mesh": {
        "description": "Joint activation — Tailscale / cross-mesh / preload",
        "slots": [
            "tailscale", "cross_mesh", "preload_all", "quantizer", "connectors",
            "frameworks", "hypertarnkappe",
        ],
        "capacity": 1.0,
        "decay": 0.88,
        "seed_activation": {"cross_mesh": 0.8, "preload_all": 0.85, "hypertarnkappe": 0.7},
    },
    "j_public": {
        "description": "Joint activation — Erfinder-Kanäle GitHub/Instagram",
        "slots": [
            "github_95guknow", "instagram_95guknow", "landing", "firebase",
            "kanon_repo", "hypertarnkappe_public",
        ],
        "capacity": 1.0,
        "decay": 0.9,
        "seed_activation": {
            "github_95guknow": 0.9,
            "instagram_95guknow": 0.85,
            "kanon_repo": 0.9,
        },
    },
    "j_quant": {
        "description": "Joint activation — adaptive substrings + M→N quant DB",
        "slots": [
            "adaptive_substring", "m_to_n", "q_table", "entwicklungsquant",
            "phrase_merge", "never_char_stream",
        ],
        "capacity": 1.0,
        "decay": 0.9,
        "seed_activation": {"adaptive_substring": 0.85, "m_to_n": 0.7, "never_char_stream": 1.0},
    },
}

# ── Higgsräume (Masse/Identität) ───────────────────────────────────────────

DEFAULT_HIGGS: Dict[str, Dict[str, Any]] = {
    "higgs_identity": {
        "description": "VEV gibt Masse/Identität dem Held-Handle und Operator-Public",
        "vev": 0.85,  # vacuum expectation value (operativ, dimensionslos)
        "couplings": {
            "held_handle": 1.0,
            "chineseh4ckerm3n": 1.0,
            "95guknow": 0.9,
            "alte_frau_kernel": 0.95,
        },
        "j_space": "j_held",
        "broken_symmetry": "anonymous_potential -> named_held",
    },
    "higgs_sinn": {
        "description": "VEV massiert Sinnquanten (Liebe/Zufriedenheit/Sinn) — Surrogate bleiben masselos relativ",
        "vev": 0.75,
        "couplings": {
            "liebesquant": 1.0,
            "zufriedenheitsquant": 0.9,
            "sinnquant": 1.0,
            "stammquant": 0.8,
            "surrogat": 0.05,  # near-zero mass — does not stabilize identity
        },
        "j_space": "j_sinn",
        "broken_symmetry": "indifferent_valence -> valued_sinn_field",
    },
    "higgs_mesh": {
        "description": "VEV massiert private Mesh-Adern (Tailscale) vs. public surface",
        "vev": 0.8,
        "couplings": {
            "tailscale": 1.0,
            "cross_mesh": 0.9,
            "hypertarnkappe": 0.95,
            "public_leak": 0.0,
        },
        "j_space": "j_mesh",
        "broken_symmetry": "open_broadcast -> private_mesh_mass",
    },
    "higgs_meister": {
        "description": "VEV der Meister-Nachricht — Integritätsmasse der Inversion",
        "vev": 0.9,
        "couplings": {
            "nachricht": 1.0,
            "integrity": 1.0,
            "inversion": 0.95,
            "no_vault_commit": 1.0,
        },
        "j_space": "j_meister",
        "broken_symmetry": "undirected_intent -> inverted_labor_probe",
    },
}


@dataclass
class JSpace:
    """Joint activation space (bounded vector over named slots)."""
    id: str
    description: str
    slots: List[str]
    capacity: float = 1.0
    decay: float = 0.9
    activation: Dict[str, float] = field(default_factory=dict)
    targeted: bool = False
    ts: float = field(default_factory=time.time)

    def activate(self, slot: str, x: float) -> None:
        if slot not in self.slots:
            self.slots.append(slot)
        cur = self.activation.get(slot, 0.0)
        self.activation[slot] = max(-self.capacity, min(self.capacity, cur + x))

    def step_decay(self) -> None:
        for s in list(self.activation.keys()):
            self.activation[s] *= self.decay
            if abs(self.activation[s]) < 1e-9:
                del self.activation[s]

    def norm_inf(self) -> float:
        if not self.activation:
            return 0.0
        return max(abs(v) for v in self.activation.values())

    def report(self, threshold: float = 0.05) -> List[Tuple[str, float]]:
        items = [(s, v) for s, v in self.activation.items() if abs(v) >= threshold]
        items.sort(key=lambda x: (-abs(x[1]), x[0]))
        return items

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "slots": list(self.slots),
            "capacity": self.capacity,
            "decay": self.decay,
            "activation": {k: round(v, 6) for k, v in self.activation.items()},
            "norm_inf": round(self.norm_inf(), 6),
            "targeted": self.targeted,
            "active_top": [{"slot": s, "a": round(v, 4)} for s, v in self.report()[:12]],
        }


@dataclass
class HiggsRaum:
    """
    Operativer Higgsraum: Skalar-VEV v verleiht Masse m_i = y_i * v
    (y = Yukawa/Kopplung analog). Kein physikalisches Higgs-Feld.
    """
    id: str
    description: str
    vev: float
    couplings: Dict[str, float]
    j_space: str
    broken_symmetry: str
    established: bool = False
    masses: Dict[str, float] = field(default_factory=dict)
    ts: float = field(default_factory=time.time)

    def establish(self) -> None:
        """Symmetriebrechung: VEV setzt Massen für gekoppelte Felder."""
        v = max(0.0, min(1.0, float(self.vev)))
        self.masses = {
            name: round(max(0.0, min(2.0, y * v)), 6)
            for name, y in self.couplings.items()
        }
        self.established = True
        self.ts = time.time()

    def mass_of(self, field_name: str) -> float:
        if not self.established:
            self.establish()
        return self.masses.get(field_name, 0.0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "description": self.description,
            "vev": self.vev,
            "couplings": self.couplings,
            "j_space": self.j_space,
            "broken_symmetry": self.broken_symmetry,
            "established": self.established,
            "masses": self.masses,
            "honesty": "operative_analogy_not_physical_higgs",
        }


class JHiggsRegistry:
    def __init__(self) -> None:
        self.j_spaces: Dict[str, JSpace] = {}
        self.higgs: Dict[str, HiggsRaum] = {}

    def target_j_spaces(self, ids: Optional[Sequence[str]] = None) -> Dict[str, Any]:
        """J-Spaces anvisieren: anlegen + seed-aktivieren."""
        want = list(ids) if ids else list(DEFAULT_J_SPACES.keys())
        out = []
        for jid in want:
            cfg = DEFAULT_J_SPACES.get(jid)
            if not cfg:
                continue
            js = JSpace(
                id=jid,
                description=cfg["description"],
                slots=list(cfg["slots"]),
                capacity=float(cfg.get("capacity", 1.0)),
                decay=float(cfg.get("decay", 0.9)),
            )
            for slot, x in (cfg.get("seed_activation") or {}).items():
                js.activate(slot, float(x))
            js.targeted = True
            self.j_spaces[jid] = js
            out.append(js.to_dict())
        return {
            "action": "target_j_spaces",
            "count": len(out),
            "ids": [j["id"] for j in out],
            "spaces": out,
            "honesty": "joint_activation_space_analogy",
        }

    def establish_higgs_raeume(self, ids: Optional[Sequence[str]] = None) -> Dict[str, Any]:
        """Higgsräume etablieren: VEV setzen, Massen berechnen."""
        want = list(ids) if ids else list(DEFAULT_HIGGS.keys())
        out = []
        for hid in want:
            cfg = DEFAULT_HIGGS.get(hid)
            if not cfg:
                continue
            h = HiggsRaum(
                id=hid,
                description=cfg["description"],
                vev=float(cfg["vev"]),
                couplings=dict(cfg["couplings"]),
                j_space=str(cfg["j_space"]),
                broken_symmetry=str(cfg["broken_symmetry"]),
            )
            h.establish()
            self.higgs[hid] = h
            out.append(h.to_dict())
        return {
            "action": "establish_higgs_raeume",
            "count": len(out),
            "ids": [h["id"] for h in out],
            "raeume": out,
            "honesty": "higgs_mass_mechanism_as_operative_analogy_only",
        }

    def couple_j_to_higgs(self) -> Dict[str, Any]:
        """
        Koppelt J-Space-Aktivierung an Higgs-Masse:
        effective_weight[slot] = activation * mass (wo mass aus gekoppeltem Higgsraum).
        """
        if not self.j_spaces:
            self.target_j_spaces()
        if not self.higgs:
            self.establish_higgs_raeume()

        couples = []
        for hid, h in self.higgs.items():
            js = self.j_spaces.get(h.j_space)
            if not js:
                continue
            for slot, a in js.activation.items():
                # match coupling key loosely
                mass = 0.0
                for cname, m in h.masses.items():
                    if cname == slot or cname in slot or slot in cname:
                        mass = max(mass, m)
                if mass <= 0 and slot in h.masses:
                    mass = h.masses[slot]
                w = round(a * mass, 6)
                if abs(w) < 1e-9:
                    continue
                couples.append({
                    "higgs": hid,
                    "j_space": h.j_space,
                    "slot": slot,
                    "activation": round(a, 6),
                    "mass": mass,
                    "weight": w,
                })
        couples.sort(key=lambda x: -abs(x["weight"]))
        return {
            "action": "couple_j_to_higgs",
            "couples": couples[:40],
            "count": len(couples),
            "top": couples[:8],
        }

    def pulse_sinn_into_j(self) -> Dict[str, Any]:
        """Optional: live Sinnquant-Scores in j_sinn speisen."""
        js = self.j_spaces.get("j_sinn")
        if not js:
            return {"ok": False, "reason": "j_sinn_not_targeted"}
        try:
            from sinn_quanten_registry import score_text
            # neutral sample + held message cues
            sample = (
                "Held chineseh4ckerm3n Liebe Vertrauen Nähe. "
                "Zufrieden ruhig. Sinn MasterSeed Integrität."
            )
            sc = score_text(sample)
            for qid, mag in (sc.get("scores") or {}).items():
                js.activate(qid, float(mag))
            return {"ok": True, "scores": sc.get("scores"), "dominant": sc.get("dominant")}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def status(self) -> Dict[str, Any]:
        return {
            "module": "j_spaces_higgs",
            "j_spaces": {k: v.to_dict() for k, v in self.j_spaces.items()},
            "higgs_raeume": {k: v.to_dict() for k, v in self.higgs.items()},
            "j_count": len(self.j_spaces),
            "higgs_count": len(self.higgs),
            "j_targeted": sum(1 for v in self.j_spaces.values() if v.targeted),
            "higgs_established": sum(1 for v in self.higgs.values() if v.established),
            "honesty": {
                "j_space": "joint_activation_vector_analogy",
                "higgs": "operative_mass_identity_analogy_not_physical_higgs",
                "bifokal": "SM_scalar_reference_vs_cognitive_operative_path",
            },
        }


_REG: Optional[JHiggsRegistry] = None


def get_registry() -> JHiggsRegistry:
    global _REG
    if _REG is None:
        _REG = JHiggsRegistry()
    return _REG


def target_j_spaces(ids: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    return get_registry().target_j_spaces(ids)


def establish_higgs_raeume(ids: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    return get_registry().establish_higgs_raeume(ids)


def couple_j_to_higgs() -> Dict[str, Any]:
    return get_registry().couple_j_to_higgs()


def status() -> Dict[str, Any]:
    return get_registry().status()


def persist(report: Optional[Dict[str, Any]] = None) -> Path:
    op = Path.home() / ".fusion" / "operator"
    op.mkdir(parents=True, exist_ok=True)
    body = report or {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **status(),
    }
    p = op / "j_spaces_higgs.json"
    p.write_text(json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    docs = Path(__file__).resolve().parents[2] / "docs" / "ops"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "J_SPACES_HIGGS.latest.json").write_text(
        json.dumps(body, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return p


def run_establish() -> Dict[str, Any]:
    """Full establish: target all J-spaces, establish all Higgsräume, couple, pulse sinn."""
    reg = get_registry()
    j = reg.target_j_spaces()
    h = reg.establish_higgs_raeume()
    sinn = reg.pulse_sinn_into_j()
    couple = reg.couple_j_to_higgs()
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": "12.1.0",
        "j_spaces": j,
        "higgs_raeume": h,
        "sinn_pulse": sinn,
        "coupling": couple,
        "status": reg.status(),
        "doc_refs": [
            "docs/meta_neural/ARCHITECTURE.md",
            "docs/dissertation/VERWEIS_BIFOKALITAET_UNIVERSUM_GEHIRN_SM.md",
            "docs/dissertation/HELD_CHINESEH4CKERM3N.md",
        ],
    }
    persist(report)
    return report


if __name__ == "__main__":
    r = run_establish()
    print(json.dumps({
        "j_count": r["j_spaces"]["count"],
        "j_ids": r["j_spaces"]["ids"],
        "higgs_count": r["higgs_raeume"]["count"],
        "higgs_ids": r["higgs_raeume"]["ids"],
        "coupling_top": r["coupling"]["top"],
        "sinn_pulse": r["sinn_pulse"],
    }, indent=2, ensure_ascii=False))
    print("persisted", Path.home() / ".fusion" / "operator" / "j_spaces_higgs.json")
