# core/SelfModifyCoreModule.py
# Version: v5.22

from __future__ import annotations

import re
import time
from typing import Any, Callable, Dict, List, Optional


class SelfModifyCoreModule:
    """Self-Modification Proposals mit Audit-Hooks und Risiko-Scoring.

    Wendet keine Datei-Diffs an (Fail-Closed). Vorschläge werden validiert,
    bewertet und nur als Metadaten protokolliert.
    """

    _HIGH_RISK = re.compile(
        r"\b(exec|eval|subprocess|os\.system|rm\s+-rf|delete|drop\s+table|"
        r"__import__|pickle\.loads)\b",
        re.IGNORECASE,
    )
    _MEDIUM_RISK = re.compile(r"\b(import\s+os|shutil\.rmtree|open\([^)]*['\"]w)\b", re.IGNORECASE)

    def __init__(self):
        self.modification_history: List[Dict[str, Any]] = []
        self.audit_hooks: Dict[str, Callable] = {}
        # Spectrum (0.0 = proposals only / read-only, 0.5 = low-risk metadata apply, 1.0 = aggressive with gates)
        # Self-regulating: autorgenerativ based on history success, audit scores, identity preservation.
        self.self_mod_spectrum: float = 0.3  # conservative default (spectrum not binary)

    def _score_risk(self, description: str, diff: str) -> str:
        blob = f"{description}\n{diff}"
        if self._HIGH_RISK.search(blob):
            return "high"
        if self._MEDIUM_RISK.search(blob):
            return "medium"
        return "low"

    def _validate_diff(self, diff: str) -> List[str]:
        if not diff.strip():
            return []
        errors: List[str] = []
        lines = diff.splitlines()
        has_hunk = any(line.startswith("@@") for line in lines)
        has_plus_minus = any(line.startswith(("+", "-")) and not line.startswith(("+++", "---")) for line in lines)
        if not has_hunk and not has_plus_minus and len(lines) > 3:
            errors.append("Diff-Format unklar (keine @@-Hunks oder +/- Zeilen)")
        if len(diff) > 50000:
            errors.append("Diff zu groß (>50k Zeichen)")
        return errors

    def propose_modification(
        self,
        description: str,
        diff: str,
        risk_level: str = "medium",
    ) -> Dict[str, Any]:
        diff_errors = self._validate_diff(diff)
        computed_risk = self._score_risk(description, diff)
        if computed_risk == "high" or risk_level == "high":
            final_risk = "high"
        elif computed_risk == "medium" or risk_level == "medium":
            final_risk = "medium"
        else:
            final_risk = "low"

        hook_results: Dict[str, Any] = {}
        for name, func in self.audit_hooks.items():
            try:
                hook_results[name] = func(description, diff)
            except Exception as exc:
                hook_results[name] = {"ok": False, "error": str(exc)}

        proposal = {
            "id": len(self.modification_history),
            "description": description,
            "diff": diff[:8000],
            "diff_truncated": len(diff) > 8000,
            "risk_level": final_risk,
            "status": "proposed",
            "diff_errors": diff_errors,
            "hook_results": hook_results,
            "ts": time.time(),
        }
        if diff_errors or final_risk == "high":
            proposal["status"] = "rejected"
        # Spectrum influence: higher spectrum allows more medium-risk proposals
        if final_risk == "medium" and self.self_mod_spectrum < 0.4:
            proposal["status"] = "rejected"  # conservative at low spectrum
        self.modification_history.append(proposal)
        # Self-regulate based on this proposal
        self.self_regulate_spectrum(
            recent_success_rate=0.85 if not diff_errors else 0.6,
            avg_audit_score=0.8 if final_risk != "high" else 0.3
        )
        return proposal

    def apply_modification(self, proposal_id: int, force: bool = False) -> Dict[str, Any]:
        if proposal_id < 0 or proposal_id >= len(self.modification_history):
            raise IndexError("Invalid proposal ID")

        proposal = self.modification_history[proposal_id]
        if proposal.get("status") == "rejected" and not force:
            raise ValueError("Proposal was rejected — use force=True to override metadata only")

        if proposal.get("risk_level") == "high" and not force:
            raise ValueError("High-risk proposal blocked (Fail-Closed). No file changes applied.")

        proposal["status"] = "applied_metadata_only"
        proposal["applied_ts"] = time.time()
        proposal["note"] = "Diff nicht auf Dateisystem angewendet (Sicherheitsrichtlinie)"
        return proposal

    def register_audit_hook(self, name: str, func: Callable) -> None:
        self.audit_hooks[name] = func

    def self_regulate_spectrum(self, recent_success_rate: float = 0.8, avg_audit_score: float = 0.7, identity_preservation: float = 0.95) -> float:
        """Autorgenerativ selbstregelnd spectrum adjustment (instead of on/off self-mod).
        Called after proposals or from tagebuch review.
        """
        # Spectrum formula: base + feedback
        adjustment = (0.2 * (recent_success_rate - 0.5)) + (0.15 * (avg_audit_score - 0.5)) + (0.1 * (identity_preservation - 0.9))
        new_s = max(0.0, min(1.0, self.self_mod_spectrum + adjustment * 0.05))
        if abs(new_s - self.self_mod_spectrum) > 0.02:
            self.self_mod_spectrum = new_s
        return self.self_mod_spectrum

    def status(self) -> Dict[str, Any]:
        return {
            "proposals": len(self.modification_history),
            "hooks": list(self.audit_hooks.keys()),
            "last": self.modification_history[-1] if self.modification_history else None,
            "self_mod_spectrum": self.self_mod_spectrum,
            "note": "Spectrum 0.0-1.0 self-regulating (no binary on/off)",
        }