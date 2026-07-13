# Heroic Core Foundation

**Layer 0 — Immutable Foundation** for the Heroic Methodology.

This package is the clean, persona-free base layer. It defines the non-negotiable principles, categorization rules, and enforcement utilities that all higher heroic modules, processes, and artifacts **must** respect.

Everything else (Peer Review, 5-stage process, archiving, self-modification, roadmaps, GUIs) lives in Layer 1+ and may evolve. **Layer 0 changes only under extreme justification and full multi-audit.**

## Contents

- `FOUNDATION.md` — Authoritative specification of immutable principles.
- `foundation.py` — Executable enforcers: Geltungskategorien validator, epistemic hygiene scanner, review gate.
- `checks/` — Pluggable rule modules (importable).

## Usage

```bash
pip install -r requirements.txt   # only if you need extras
python -m foundation --help
```

Or import in Python:

```python
from foundation import (
    validate_geltungskategorien,
    scan_epistemic_hygiene,
    run_foundation_gate
)

issues = scan_epistemic_hygiene(text)
```

## Integration

This foundation is the reference for:
- Fusion Hero OS
- Dashboard /heroic
- All future heroic programs and books

All significant outputs should pass the foundation gate before promotion.

## Version

v1.0 — 2026-06-27 — Initial clean extraction of Layer 0.

## Philosophy

Clarity over charisma. Evidence over narrative. Explicit categories over silent upgrades. Self-criticism as default posture. Nothing is sacred except the rules that protect inquiry.
