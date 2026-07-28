"""
Ops vocabulary — deploy=private · push=public · merge=both (dual timeline).

Canonical language for Fusion Hero OS v10.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "ops_vocabulary.yaml"

__all__ = [
    "OPS",
    "load_ops",
    "meaning_of",
    "status",
    "OPS_DEPLOY",
    "OPS_PUSH",
    "OPS_MERGE",
]

OPS_DEPLOY = "deploy"
OPS_PUSH = "push"
OPS_MERGE = "merge"

# Hard map (code identity — even without YAML)
OPS = {
    OPS_DEPLOY: "private",
    OPS_PUSH: "public",
    OPS_MERGE: "both_via_timeline",
}


def load_ops() -> dict[str, Any]:
    if not CONFIG.exists():
        return {
            "operations": {
                "deploy": {"meaning": "private"},
                "push": {"meaning": "public"},
                "merge": {"meaning": "both_via_timeline"},
            },
            "mapping_table": dict(OPS),
        }
    try:
        import yaml

        return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    except Exception:
        return {"mapping_table": dict(OPS)}


def meaning_of(op: str) -> str:
    op = (op or "").strip().lower()
    data = load_ops()
    table = data.get("mapping_table") or OPS
    if op in table:
        return str(table[op])
    ops = data.get("operations") or {}
    if op in ops:
        return str(ops[op].get("meaning") or OPS.get(op, "unknown"))
    return OPS.get(op, "unknown")


def status() -> dict[str, Any]:
    data = load_ops()
    return {
        "ok": True,
        "platform": "10.0.0",
        "policy": "pseudo_inhouse_only",
        "freemium": False,
        "vocabulary": {
            "deploy": "private",
            "push": "public",
            "merge": "both_via_timeline",
        },
        "german": {
            "deploy": "privat",
            "push": "öffentlich",
            "merge": "beide — privat+öffentlich über Timeline verbinden",
        },
        "config": str(CONFIG) if CONFIG.exists() else None,
        "operations": data.get("operations"),
    }


def main() -> int:
    print(json.dumps(status(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
