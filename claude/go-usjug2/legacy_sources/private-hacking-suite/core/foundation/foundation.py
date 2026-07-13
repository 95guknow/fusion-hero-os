#!/usr/bin/env python3
"""
Private Hacking Suite - Layer 0 Foundation
Cleaned and adapted for private middle-out restructure.
Integrates with springloop_energy for contraction checks (see layers/layer0).
"""

from __future__ import annotations
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional

# Official categories (order matters for strictness)
CATEGORIES = ["Satz", "Bedingt", "Modell", "Axiomatisch", "Fragment"]

# Common signals of problematic elevation
# Keep deliberately conservative: require stronger claim language
METAPHOR_PROOF_PATTERNS = [
    r"\b(wie|als ob|gleichsam|sozusagen|quasi)\b[^.]{0,80}\b(beweist|belegt|zeigt (sich )?als|impliziert|ist (daher|folglich))\b",
]

MODAL_COLLAPSE_PATTERNS = [
    r"\b(könnte|können|might|could|may|potenziell)\b[^.]{0,70}\b(ist|bedeutet (daher|folglich)|zeigt sich (als|dass))\b",
]

UNLABELED_CLAIM_PATTERNS = [
    r"\b(daher|folglich|deshalb|therefore|thus|hence)\b[^.]*\.",
]

GELTUNG_TAG_RE = re.compile(
    r"\b(Satz|Bedingt|Modell|Axiomatisch|Fragment)\b", re.IGNORECASE
)

@dataclass
class Finding:
    kind: str
    line: int
    snippet: str
    severity: str = "medium"   # low | medium | high | critical

@dataclass
class FoundationReport:
    passed: bool
    findings: List[Finding] = field(default_factory=list)
    category_counts: Dict[str, int] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        cats = ", ".join(f"{k}:{v}" for k, v in self.category_counts.items()) or "none"
        return f"Foundation Gate: {status} | Categories seen: {cats} | Issues: {len(self.findings)}"

def _read_lines(text: str) -> List[str]:
    return text.splitlines()

def scan_epistemic_hygiene(text: str) -> List[Finding]:
    """Detect metaphor-as-proof and modal collapse."""
    findings: List[Finding] = []
    lines = _read_lines(text)
    for i, line in enumerate(lines, 1):
        low = line.lower()
        for pat in METAPHOR_PROOF_PATTERNS:
            if re.search(pat, low):
                findings.append(Finding("metaphor_as_proof", i, line[:160].strip(), "high"))
        for pat in MODAL_COLLAPSE_PATTERNS:
            if re.search(pat, low):
                findings.append(Finding("modal_collapse", i, line[:160].strip(), "high"))
        for pat in UNLABELED_CLAIM_PATTERNS:
            if re.search(pat, low) and not GELTUNG_TAG_RE.search(line):
                findings.append(Finding("unlabeled_conclusion", i, line[:160].strip(), "medium"))
    return findings

def validate_geltungskategorien(text: str) -> Dict[str, int]:
    """Count explicit category labels. Does not auto-infer."""
    counts: Dict[str, int] = {c: 0 for c in CATEGORIES}
    for m in GELTUNG_TAG_RE.finditer(text):
        cat = m.group(1).capitalize()
        if cat in counts:
            counts[cat] += 1
    return counts

def check_foundation_gate(text: str, require_explicit: bool = True) -> FoundationReport:
    """
    Full Layer 0 gate.
    require_explicit=True means at least one labeled category must appear for non-trivial content.
    """
    findings = scan_epistemic_hygiene(text)
    cat_counts = validate_geltungskategorien(text)

    notes = []
    passed = True

    if require_explicit:
        total_labeled = sum(cat_counts.values())
        if total_labeled == 0 and len(text) > 200:
            findings.append(Finding(
                "no_geltung_labels",
                0,
                "No explicit Geltungskategorie labels found in substantial text.",
                "medium"
            ))
            notes.append("Consider labeling key claims with Satz / Bedingt / Modell / Axiomatisch / Fragment.")

    # Critical if any high-severity hygiene violations
    critical = any(f.severity in ("high", "critical") for f in findings)
    if critical:
        passed = False

    if findings and any(f.kind == "no_geltung_labels" for f in findings):
        passed = False

    return FoundationReport(
        passed=passed,
        findings=findings,
        category_counts={k: v for k, v in cat_counts.items() if v > 0},
        notes=notes
    )

# ---------------- CLI ----------------

def main(argv: Optional[List[str]] = None) -> int:
    argv = argv or sys.argv[1:]
    if not argv or argv[0] in ("-h", "--help"):
        print("Usage: python foundation.py <file.md|file.txt> [--strict]")
        print("       python foundation.py --stdin [--strict]")
        return 0

    strict = "--strict" in argv
    argv = [a for a in argv if a != "--strict"]

    if argv[0] == "--stdin":
        text = sys.stdin.read()
        name = "<stdin>"
    else:
        path = Path(argv[0])
        if not path.exists():
            print(f"File not found: {path}")
            return 2
        text = path.read_text(encoding="utf-8", errors="replace")
        name = path.name

    report = check_foundation_gate(text, require_explicit=strict or True)

    print(f"\n=== Heroic Core Foundation Gate ===")
    print(f"Input: {name}")
    print(report.summary())

    if report.findings:
        print("\nFindings:")
        for f in report.findings:
            print(f"  [{f.severity.upper():8}] L{f.line:4d} {f.kind:22s} | {f.snippet}")

    if report.notes:
        print("\nNotes:")
        for n in report.notes:
            print(f"  - {n}")

    print("\n" + ("✓ PASSES FOUNDATION" if report.passed else "✗ FAILS FOUNDATION"))

    return 0 if report.passed else 1

if __name__ == "__main__":
    sys.exit(main())
