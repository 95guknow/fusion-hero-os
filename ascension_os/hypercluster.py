# -*- coding: utf-8 -*-
"""AscensionHypercluster — Hyperclusterup Zitterpolymesh als Ausführungsschicht
des AscensionOS-Tracks, betrieben unter der Senfkorn Holding UG.

Zweck (ehrlich, keine Magie):

* Der Hypercluster ist der bereits existierende PVHT-Scheduler
  (:mod:`fusion_hero_os.core.zitterpolymesh`) mit vier Lanes CPU/MEM/GPU/QPU.
  Dieses Modul stellt jede *Ascension* (Kernkomponente des ``ascension_os``-
  Tracks) als Workflow-Knoten auf einer Lane bereit und lässt sie flüssig,
  dependency-getrieben über den Cluster laufen.
* "In allen Ascensionen einrichten und operationalisieren" heißt konkret:
  für jede in der Config deklarierte Ascension-Einheit eine Readiness-Probe
  über den Cluster fahren (Modul importierbar? Entrypoint vorhanden?) und den
  Betriebszustand ehrlich melden — ``operational`` / ``degraded`` /
  ``blocked_consent``. Nichts wird als betriebsbereit gemeldet, das es nicht
  ist (kein Fake-Erfolg, konsistent mit dem Rest des Repos).
* **Consent bleibt Layer 0:** Ascension-Einheiten, die personenbezogene Daten
  berühren (Sisyphos-Last, Psycholyse-Logs, Expositions-Transkripte), laufen
  ohne aktiven Consent-Grant **fail-closed** (``blocked_consent``) — dieselbe
  Disziplin wie :mod:`ascension_os.consent_gate`.
* **Governance:** Der Betreiber/Owner (Senfkorn Holding UG) ist ein
  deklariertes Config-Feld — reine Zuordnung, kein Rechts-/Registerdokument.

Nur Stdlib + die bereits vorhandenen Repo-Module als harte Abhängigkeit;
``yaml`` wird optional erkannt (Fallback auf eingebaute Default-Config).
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from fusion_hero_os.core.zitterpolymesh import (
    LaneKind,
    LaneProfile,
    ZitterPolyMesh,
    detect_lanes,
)

__all__ = [
    "AscensionUnit",
    "AscensionHypercluster",
    "DEFAULT_GOVERNANCE",
    "DEFAULT_UNITS",
    "CONFIG_PATH",
]

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "ascension_os" / "config" / "hypercluster.yaml"

DEFAULT_GOVERNANCE: Dict[str, Any] = {
    "owner": "Senfkorn Holding UG",
    "track": "ascension",
    "platform_version": "12.0.0",
    "consent_required_for_personal_data": True,
    "note": (
        "Owner ist eine deklarierte Betreiber-Zuordnung (Config-Label), "
        "kein Rechts-/Registerdokument."
    ),
}


@dataclass(frozen=True)
class AscensionUnit:
    """Eine Ascension als Cluster-Knoten."""

    name: str
    lane: LaneKind
    module: str
    entrypoint: str
    requires_consent: bool = False
    deps: tuple = ()

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "lane": self.lane.value,
            "module": self.module,
            "entrypoint": self.entrypoint,
            "requires_consent": self.requires_consent,
            "deps": list(self.deps),
        }


# Die vier Lanes decken die Natur der Ascension-Arbeit ab:
#   CPU  — Kern-/Consent-/Tracker-Logik
#   MEM  — persistenter Zustand (Sisyphos, Stage-9)
#   GPU  — generationale Evolution (rechenlastig)
#   QPU  — QUBO-Optimierung (Annealing-Simulator)
DEFAULT_UNITS: List[AscensionUnit] = [
    AscensionUnit(
        "consent-gate", LaneKind.CPU,
        "ascension_os.consent_gate", "AscensionConsentGate",
    ),
    AscensionUnit(
        "ascension-core", LaneKind.CPU,
        "ascension_os.core.ascension_core", "AscensionCore",
        deps=("consent-gate",),
    ),
    AscensionUnit(
        "persistent-sisyphos", LaneKind.MEM,
        "ascension_os.core.persistent_sisyphos", "PersistentSisyphosCycle",
        requires_consent=True, deps=("consent-gate",),
    ),
    AscensionUnit(
        "stage9-tracker", LaneKind.MEM,
        "ascension_os.core.stage9_tracker", "Stage9AscensionTracker",
        requires_consent=True, deps=("consent-gate",),
    ),
    AscensionUnit(
        "generational-evolution", LaneKind.GPU,
        "ascension_os.evolution.generational_engine", "GenerationalEvolutionEngine",
        deps=("ascension-core",),
    ),
    AscensionUnit(
        "qubo-optimizer", LaneKind.QPU,
        "ascension_os.core.qubo_ascension_optimizer", "QUBOAscensionOptimizer",
        deps=("ascension-core",),
    ),
]


def _load_config() -> Dict[str, Any]:
    """Config aus YAML lesen; Fallback auf eingebaute Defaults."""
    if not CONFIG_PATH.is_file():
        return {"governance": dict(DEFAULT_GOVERNANCE), "units": None}
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except ImportError:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    gov = {**DEFAULT_GOVERNANCE, **(data.get("governance") or {})}
    return {"governance": gov, "units": data.get("units")}


def _units_from_config(spec: Optional[List[Dict[str, Any]]]) -> List[AscensionUnit]:
    if not spec:
        return list(DEFAULT_UNITS)
    units: List[AscensionUnit] = []
    for u in spec:
        units.append(
            AscensionUnit(
                name=u["name"],
                lane=LaneKind(u.get("lane", "cpu")),
                module=u["module"],
                entrypoint=u["entrypoint"],
                requires_consent=bool(u.get("requires_consent", False)),
                deps=tuple(u.get("deps", [])),
            )
        )
    return units


def _probe_unit(unit: AscensionUnit, consent_ok: bool) -> Dict[str, Any]:
    """Readiness-Probe für eine Ascension. Wirft nie — meldet ehrlich Zustand."""
    result: Dict[str, Any] = {
        "unit": unit.name,
        "lane": unit.lane.value,
        "module": unit.module,
        "requires_consent": unit.requires_consent,
        "importable": False,
        "entrypoint_present": False,
        "error": None,
    }
    try:
        mod = importlib.import_module(unit.module)
        result["importable"] = True
        result["entrypoint_present"] = hasattr(mod, unit.entrypoint)
    except Exception as exc:  # noqa: BLE001 — Probe darf den Cluster nie reißen
        result["error"] = f"{type(exc).__name__}: {exc}"[:180]

    if unit.requires_consent and not consent_ok:
        # Layer-0-Regel: personenbezogene Ascension ohne Grant = fail-closed
        result["status"] = "blocked_consent"
    elif result["importable"] and result["entrypoint_present"]:
        result["status"] = "operational"
    else:
        result["status"] = "degraded"
    result["operational"] = result["status"] == "operational"
    return result


@dataclass
class AscensionHypercluster:
    """Bindet den Zitterpolymesh-Cluster an den Ascension-Track."""

    governance: Dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_GOVERNANCE))
    units: List[AscensionUnit] = field(default_factory=lambda: list(DEFAULT_UNITS))
    lanes: Optional[Dict[LaneKind, LaneProfile]] = None

    @classmethod
    def from_config(cls, lanes: Optional[Dict[LaneKind, LaneProfile]] = None) -> "AscensionHypercluster":
        cfg = _load_config()
        return cls(
            governance=cfg["governance"],
            units=_units_from_config(cfg["units"]),
            lanes=lanes,
        )

    def _mesh(self, consent_ok: bool) -> ZitterPolyMesh:
        mesh = ZitterPolyMesh(lanes=self.lanes)
        for unit in self.units:
            mesh.add_task(
                name=unit.name,
                lane=unit.lane,
                fn=(lambda ctx, _u=unit: _probe_unit(_u, consent_ok)),
                deps=unit.deps,
                retries=1,
            )
        return mesh

    def validate(self) -> List[str]:
        """DAG-Validierung (Zyklen/unbekannte Deps/Lanes) ohne Ausführung."""
        return self._mesh(consent_ok=False).validate()

    def operationalize(self, *, consent_ok: bool = False, timeout: float = 120.0) -> Dict[str, Any]:
        """Alle Ascensionen über den Hypercluster anfahren und Zustand melden.

        ``consent_ok=False`` (Default, fail-closed): personenbezogene Einheiten
        werden als ``blocked_consent`` gemeldet und **nicht** als betriebsbereit
        ausgewiesen. Ein echter Grant kommt aus ``ascension_os.consent_gate`` /
        ``fusion_hero_os.meta.consent`` — dieses Flag spiegelt nur dessen Ergebnis.
        """
        report = self._mesh(consent_ok=consent_ok).run(timeout=timeout)

        units_report = {name: rec.get("result") or {"status": rec.get("status")}
                        for name, rec in report["tasks"].items()}
        statuses = [u.get("status") for u in units_report.values()]
        summary = {
            "operational": statuses.count("operational"),
            "degraded": statuses.count("degraded"),
            "blocked_consent": statuses.count("blocked_consent"),
            "total": len(statuses),
        }
        return {
            "ok": report["ok"],
            "governance": self.governance,
            "consent_ok": consent_ok,
            "lanes": report["lanes"],
            "ascensions": units_report,
            "summary": summary,
            "wall_sec": report["wall_sec"],
            # betriebsbereit heißt: alle nicht-consent-gesperrten Einheiten operational
            "fully_operational": summary["degraded"] == 0,
        }

    def status(self) -> Dict[str, Any]:
        """Statischer Überblick ohne Cluster-Lauf (Lanes + Einheiten + Owner)."""
        lanes = self.lanes or detect_lanes()
        return {
            "ok": True,
            "governance": self.governance,
            "lanes": {k.value: v.as_dict() for k, v in lanes.items()},
            "units": [u.as_dict() for u in self.units],
            "count": len(self.units),
        }


def _cli(argv: Optional[Iterable[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="AscensionHypercluster (Zitterpolymesh × AscensionOS)")
    ap.add_argument("--status", action="store_true", help="Lanes + Einheiten + Owner")
    ap.add_argument("--validate", action="store_true", help="DAG validieren")
    ap.add_argument("--operationalize", action="store_true", help="alle Ascensionen anfahren")
    ap.add_argument("--consent-ok", action="store_true",
                    help="setzt aktiven Consent-Grant voraus (Default: fail-closed)")
    args = ap.parse_args(list(argv) if argv is not None else None)

    hc = AscensionHypercluster.from_config()

    if args.validate:
        order = hc.validate()
        print(json.dumps({"ok": True, "order": order}, indent=2, ensure_ascii=False))
        return 0
    if args.operationalize:
        report = hc.operationalize(consent_ok=args.consent_ok)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["ok"] else 1
    print(json.dumps(hc.status(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_cli())
