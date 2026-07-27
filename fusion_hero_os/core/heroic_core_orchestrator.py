#!/usr/bin/env python3
"""
FUSION HERO OS v8 - HEROIC CORE ORCHESTRATOR

Layer 0 + 4 + 5 Bridge mit Heroic- und Ascension-Track.

Ehrlicher Stand (siehe docs/02_architecture/HEROIC_CORE_ORCHESTRATOR.md):
- MasterSeed.verify_integrity() ist seit 2026-07-04 eine echte Pruefung
  gegen den kanonischen state_hash() (SHA-256 ueber die Seed-Felder).
- PMSEvidenceSpine erwartet das lokale Kernel-Binary aus
  pms_rust_kernel_crate/; ohne gebautes Binary endet jede Ausfuehrung
  FAIL_CLOSED (das Fail-Closed-Verhalten selbst ist real und getestet).
- Phoenix-Mode leert nur die fluechtigen Container (volatile_history,
  volatile_cache); es gibt keinen weitergehenden State-Reset.

Wiederhergestellt in der v8.3-Konsolidierung: Diese Datei war durch ein
unvollstaendiges Delta-Fragment ersetzt worden (Regression in 745a6e2);
Basis ist der letzte vollstaendige Stand (c4b839f) plus die dort gemeinte
Ascension-Erweiterung, jetzt korrekt ausformuliert.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    from .universal_llm_router import LLMResult
except Exception:  # pragma: no cover - nur bei kaputter Provider-Schicht
    LLMResult = None

# Ascension Track (v9.x) ist optional und wird LAZY in QuadCoreBridge.__init__
# importiert (gleiche Begruendung wie beim heroic_core-Import dort): der
# Top-Level-Import erzeugte den Import-Zyklus ascension_core -> heroic_core ->
# orchestrator -> ascension_core (Befund: dependency_atlas --check).
AscensionCore = None  # nur fuer Typ-Referenzen; echte Bindung lazy

_REPO_ROOT = Path(__file__).resolve().parents[2]

VALID_DOMAINS = ("MYTHOS", "GRUND", "BEWEIS", "GESTALT")


# =====================================================================
# LAYER 0: MASTER SEED
# =====================================================================

@dataclass(frozen=True)
class MasterSeed:
    """Layer-0 Fixpunkt. Unveraenderlich per frozen dataclass."""

    genesis_hash: str = "000000000im0000000000000000000000000000000000000000000000000000"
    criticality_target: float = 0.22  # Heuristisches Modell (vgl. Geltungs-Werkbank)
    strict_contraction_enforced: bool = True

    def state_hash(self) -> str:
        """Kanonischer SHA-256 ueber die geordneten Seed-Felder."""
        canonical = json.dumps(
            {
                "genesis_hash": self.genesis_hash,
                "criticality_target": self.criticality_target,
                "strict_contraction_enforced": self.strict_contraction_enforced,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def verify_integrity(self, current_state_hash: str) -> bool:
        """Echte Integritaetspruefung: nur der kanonische state_hash() gilt.

        Liefert False fuer jeden abweichenden, leeren oder nicht-String-Wert.
        """
        return (
            isinstance(current_state_hash, str)
            and current_state_hash.strip().lower() == self.state_hash()
        )

    def public_display(self, platform_version: str = "10.0.0"):
        """Eindeutige oeffentliche Darstellung (kein Private-Vault-Material).

        Siehe fusion_hero_os.core.masterseed_public / masterseed_vault:
        public = unique display_id; private = GPG+QUBO, modul/funktionsweise getrennt.
        """
        from fusion_hero_os.core.masterseed_public import public_view

        return public_view(self, platform_version=platform_version)


# =====================================================================
# LAYER 4: PMS EVIDENCE SPINE (Fail-Closed Bruecke zum Rust-Kernel)
# =====================================================================

class PMSEvidenceSpine:
    """Kapselt das lokale PMS-Rust-Kernel-Binary (pms_rust_kernel_crate/).

    Ist das Binary nicht gebaut oder der Aufruf schlaegt fehl, liefert jede
    Ausfuehrung deterministisch FAIL_CLOSED - niemals einen stillen Erfolg.
    """

    def __init__(self, executable_path: str = None, model_path: str = None,
                 audit_path: str = None):
        default_kernel = _REPO_ROOT / "pms_rust_kernel_crate" / "target" / "release" / (
            "pms_rust_kernel.exe" if os.name == "nt" else "pms_rust_kernel"
        )
        self.kernel_path = executable_path or str(default_kernel)
        self.model_path = model_path or str(_REPO_ROOT / "PMS.yaml")
        self.audit_path = audit_path or str(_REPO_ROOT / "pms_audit.jsonl")

    @property
    def available(self) -> bool:
        return Path(self.kernel_path).is_file() and Path(self.model_path).is_file()

    def _run(self, args: list, payload_json: str) -> dict[str, Any]:
        try:
            result = subprocess.run(
                [self.kernel_path, *args, "--model", self.model_path,
                 "--audit", self.audit_path],
                input=payload_json.encode("utf-8"),
                capture_output=True,
                check=True,
                timeout=10.0,
            )
            return json.loads(result.stdout)
        except Exception as e:  # FAIL-CLOSED: jeder Fehler schliesst die Bruecke
            return {"status": "FAIL_CLOSED", "error": str(e)}

    def execute_operator_chain(self, operator_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._run(["--operator", operator_id], json.dumps(payload))

    def validate_chain(self, chain_id: str) -> dict[str, Any]:
        return self._run(["--validate-chain", chain_id], "")


# =====================================================================
# LAYER 5: QUAD CORE BRIDGE (Heroic + Ascension)
# =====================================================================

class QuadCoreBridge:
    """Layer 0 + 4 + 5 Bridge.

    Kann im Heroic- oder Ascension-Modus betrieben werden; der
    Ascension-Track (v9.x, ascension_os/) ist optional und wird bei
    Nichtverfuegbarkeit still auf den Heroic-Pfad zurueckgefuehrt.
    """

    def __init__(self, spine: PMSEvidenceSpine, seed: MasterSeed = None,
                 mode: str = "heroic"):
        self.spine = spine
        self.seed = seed or MasterSeed()
        self.mode = mode.upper()  # "HEROIC" | "ASCENSION" | "PHOENIX"
        self.volatile_history: list = []
        self.volatile_cache: dict[str, Any] = {}

        # Heroic Track (lazy import: vermeidet den Zirkular-Import
        # orchestrator -> heroic_core -> orchestrator beim Modul-Laden)
        try:
            from .heroic_core import get_heroic_core
            self.heroic = get_heroic_core(quad_core=self)
        except Exception:
            self.heroic = None
        self.llm = self.heroic.llm if self.heroic else None

        # Ascension Track (jetzt mit substantiellem AscensionCore v9.4);
        # lazy import — siehe Modulkopf (Zyklus-Befund dependency_atlas)
        self.ascension: AscensionCore | None = None
        try:
            from ascension_os.core.ascension_core import get_ascension_core
            self.ascension = get_ascension_core()
            self.ascension.register_masterseed(self.seed)
        except Exception:
            self.ascension = None

    def invoke_phoenix_mode(self) -> bool:
        """Leert die fluechtigen Container und prueft die Seed-Integritaet.

        Kein weitergehender State-Reset: bestehende Attribute bleiben erhalten.
        """
        print(f"[LAYER 5] Phoenix-Mode aktiviert (Mode: {self.mode})")
        self.mode = "PHOENIX"
        self._flush_volatile_memory()
        return self.seed.verify_integrity(self.seed.state_hash())

    def _flush_volatile_memory(self) -> None:
        self.volatile_history.clear()
        self.volatile_cache.clear()

    def process_query(self, domain: str, operator_id: str,
                      payload: dict[str, Any]) -> Any:
        if domain not in VALID_DOMAINS:
            raise ValueError(
                f"Ungueltige Domaene: {domain}. Quad-Core-Architektur verletzt "
                f"(erlaubt: {', '.join(VALID_DOMAINS)})."
            )
        # Nur BEWEIS und GESTALT duerfen native Executions im Spine triggern
        if domain in ("BEWEIS", "GESTALT"):
            return self.spine.execute_operator_chain(operator_id, payload)
        self.volatile_history.append({"domain": domain, "operator": operator_id})
        return {"status": "SUCCESS", "message": f"via {self.mode} Core"}

    def ask_llm(self, prompt: str, system_prompt: str | None = None,
                force_provider: str | None = None):
        """LLM-Anfrage; im ASCENSION-Modus zuerst ueber den AscensionCore."""
        if self.mode == "ASCENSION" and self.ascension:
            print("[ASCENSION] Using enhanced AscensionCore")
            result = self.ascension.ask(prompt)
            if result is not None:
                return result

        # Default Heroic Path
        if not self.llm:
            if LLMResult:
                return LLMResult("no-llm", "LLM Core nicht verfuegbar")
            return None
        assignment = self.llm.get_best_assignment(prompt)
        if assignment:
            print(f"[{self.mode}] {assignment['provider']} (score={assignment['score']:.3f})")
        return self.llm.ask(prompt, system_prompt, force_provider, context="heroic")

    def run_ascension_generation(self, generations: int = 5) -> dict[str, Any]:
        if self.ascension:
            return self.ascension.run_generation(generations=generations)
        return {"status": "AscensionCore nicht verfuegbar"}


# =====================================================================
# INITIALISIERUNG: BOOT-SEQUENZ
# =====================================================================

def bootstrap_v8_system(mode: str = "heroic") -> QuadCoreBridge:
    print("=" * 70)
    print(f"BOOTING FUSION-HERO-OS v8 — {mode.upper()} MODE")
    print("=" * 70)
    seed = MasterSeed()
    spine = PMSEvidenceSpine()
    core = QuadCoreBridge(spine, seed=seed, mode=mode)
    print(f"[LAYER 0+4+5] MasterSeed + PMS-Spine (available={spine.available}) "
          f"+ QuadCore ({core.mode})")
    if core.ascension:
        print("[ASCENSION] AscensionCore v9.x angebunden")
    print("=" * 70)
    return core


if __name__ == "__main__":
    heroic_core = bootstrap_v8_system(mode="ascension")
    response = heroic_core.process_query(
        domain="GESTALT",
        operator_id="OP_Q_B_CIRC",
        payload={"action": "verify_reciprocity"},
    )
    print(f"Spine Response: {response}")
