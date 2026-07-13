#!/usr/bin/env python3
"""Layer-by-layer processing — delegates to core.suite_pipeline when available."""
from __future__ import annotations

import json
import sys
from pathlib import Path

_CORE = Path(__file__).resolve().parent.parent / "core"
if str(_CORE) not in sys.path:
    sys.path.insert(0, str(_CORE))

from suite_pipeline import run_full_pipeline  # noqa: E402


def main() -> int:
    result = run_full_pipeline(verbose=True)
    print(json.dumps(result.get("summary", {}), indent=2))
    if not result.get("ok"):
        print("Pipeline failed:", result.get("error"))
        return 1
    print(f"\n=== {result['layers_processed']} layers processed COEVOLUTIONÄR ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())