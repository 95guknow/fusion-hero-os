"""
deploy = private

Runs private-only operations: MasterSeed vault seal, dual-timeline train,
creative local artifacts. Never git-pushes to public remote.
"""
from __future__ import annotations

import json
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

from fusion_hero_os.core.ops_vocabulary import OPS_DEPLOY, meaning_of

__all__ = ["deploy", "status"]


def status() -> dict[str, Any]:
    return {
        "ok": True,
        "operation": OPS_DEPLOY,
        "meaning": meaning_of(OPS_DEPLOY),
        "german": "privat",
        "public_remote": False,
    }


def deploy(
    *,
    seal_masterseed: bool = True,
    train_timeline: bool = True,
    inside_out_inventory: bool = False,
) -> dict[str, Any]:
    """Private deploy: local vault + local training. No public push."""
    t0 = time.time()
    out: dict[str, Any] = {
        "operation": OPS_DEPLOY,
        "meaning": "private",
        "started_at": datetime.now(UTC).isoformat(),
        "steps": [],
    }
    if inside_out_inventory:
        try:
            from fusion_hero_os.core.inside_out_inventory import run_inventory

            inv = run_inventory(write=True)
            out["steps"].append(
                {
                    "step": "inside_out_inventory",
                    "ok": bool(inv.get("ok")),
                    "files": (inv.get("counts") or {}).get("files"),
                    "items": (inv.get("counts") or {}).get("items"),
                    "paths": inv.get("paths"),
                }
            )
        except Exception as e:  # noqa: BLE001
            out["steps"].append({"step": "inside_out_inventory", "ok": False, "error": str(e)[:200]})

    if seal_masterseed:
        try:
            from fusion_hero_os.core.masterseed_vault import seal_all_modules, export_public_display

            # public display file is OK locally; private shards stay local
            pub = export_public_display()
            sealed = seal_all_modules()
            out["steps"].append(
                {
                    "step": "masterseed_vault",
                    "ok": True,
                    "public_display_id": pub.get("display_id"),
                    "sealed_count": sealed.get("sealed_count"),
                    "note": "private shards only under ~/.fusion/masterseed/private",
                }
            )
        except Exception as e:  # noqa: BLE001
            out["steps"].append({"step": "masterseed_vault", "ok": False, "error": str(e)[:200]})

    if train_timeline:
        try:
            from fusion_hero_os.core.dual_timeline_training import run_auto_train

            tr = run_auto_train(write=True)
            out["steps"].append(
                {
                    "step": "dual_timeline_train",
                    "ok": bool(tr.get("ok")),
                    "files": tr.get("files"),
                    "samples": tr.get("samples"),
                    "paths": tr.get("paths"),
                    "note": "training outputs private under ~/.fusion/training",
                }
            )
        except Exception as e:  # noqa: BLE001
            out["steps"].append({"step": "dual_timeline_train", "ok": False, "error": str(e)[:200]})

    out["ok"] = all(s.get("ok") for s in out["steps"]) if out["steps"] else True
    out["duration_sec"] = round(time.time() - t0, 2)
    out["ended_at"] = datetime.now(UTC).isoformat()

    man = Path.home() / ".fusion" / "ops" / "deploy_latest.json"
    man.parent.mkdir(parents=True, exist_ok=True)
    man.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    out["manifest"] = str(man)
    return out


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="deploy = private")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--no-seal", action="store_true")
    ap.add_argument("--no-train", action="store_true")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    r = deploy(seal_masterseed=not args.no_seal, train_timeline=not args.no_train)
    print(json.dumps(r, indent=2, ensure_ascii=False)[:4000])
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
