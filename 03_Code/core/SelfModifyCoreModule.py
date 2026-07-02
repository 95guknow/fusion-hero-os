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
        self.modification_history.append(proposal)
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

    def status(self) -> Dict[str, Any]:
        return {
            "proposals": len(self.modification_history),
            "hooks": list(self.audit_hooks.keys()),
            "last": self.modification_history[-1] if self.modification_history else None,
        }