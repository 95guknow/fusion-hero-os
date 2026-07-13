#!/usr/bin/env python3
"""Führt Claude-Science-Audit über formale Heroik-Mathematik + Wissenschaftsansätze aus."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / "03_Code"
sys.path.insert(0, str(CORE))

from core.heroic_science_audit import run_audit, status  # noqa: E402


def main() -> None:
    print("=== Heroic Science Audit ===")
    print(json.dumps(status(), indent=2, ensure_ascii=False))
    report = run_audit(max_workers=2, save=True, desktop_copy=True)
    print("\n=== Summary ===")
    print(json.dumps(report["summary"], indent=2, ensure_ascii=False))
    print(f"\nReport: {report.get('report_md')}")
    if report.get("desktop_path"):
        print(f"Desktop: {report['desktop_path']}")


if __name__ == "__main__":
    main()