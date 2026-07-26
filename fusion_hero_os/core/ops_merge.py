# -*- coding: utf-8 -*-
"""
merge = both (private + public) connected via dual + virtual timeline (t ∥ τ ∥ v)

Does not leak private shard payloads into git. Produces a merge manifest
linking public display identities to private module/function refs and
timeline axes. Virtual axis is labor sandbox only (BIG ALPHA re-enabled).
"""
from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fusion_hero_os.core.ops_vocabulary import OPS_MERGE, meaning_of

__all__ = ["merge_both", "status"]

PLATFORM = "12.1.0"


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "operation": OPS_MERGE,
        "meaning": meaning_of(OPS_MERGE),
        "german": "beide — privat und öffentlich über Timeline verbinden (Fusion↔Musion)",
        "platform": PLATFORM,
        "cycle": "BIG_ALPHA",
        "axes": {
            "t": "real",
            "tau": "imaginary_structural_heroic",
            "v": "virtual_heroic_scenario",
        },
        "alias": "fusion_musion_merge",
    }


def merge_both(
    *,
    run_deploy: bool = True,
    include_timeline: bool = True,
) -> Dict[str, Any]:
    """Connect private deploy state with public presentation via dual timeline."""
    t0 = time.time()
    out: Dict[str, Any] = {
        "operation": OPS_MERGE,
        "meaning": "both_via_timeline",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "links": [],
        "steps": [],
    }

    # --- public side ---
    public: Dict[str, Any] = {}
    try:
        from fusion_hero_os.core.masterseed_public import public_view

        public = public_view().to_dict()
        out["steps"].append({"step": "public_masterseed", "ok": True, "display_id": public.get("display_id")})
    except Exception as e:  # noqa: BLE001
        out["steps"].append({"step": "public_masterseed", "ok": False, "error": str(e)[:160]})

    # --- private side (refs only, no payloads) ---
    private_refs: List[Dict[str, Any]] = []
    if run_deploy:
        try:
            from fusion_hero_os.core.ops_deploy import deploy

            dep = deploy(seal_masterseed=True, train_timeline=include_timeline)
            out["steps"].append(
                {
                    "step": "deploy_private",
                    "ok": dep.get("ok"),
                    "manifest": dep.get("manifest"),
                }
            )
        except Exception as e:  # noqa: BLE001
            out["steps"].append({"step": "deploy_private", "ok": False, "error": str(e)[:160]})

    try:
        from fusion_hero_os.core.masterseed_vault import list_module_split, status as vst

        vs = vst()
        for entry in list_module_split():
            mod = entry.get("module")
            for fn in entry.get("functions") or []:
                private_refs.append(
                    {
                        "module": mod,
                        "function": fn,
                        "shard_rel": (
                            f"private/modules/{str(mod).replace('.', '_')}/"
                            f"functions/{str(fn).replace('.', '_')}.shard.gpg"
                        ),
                        # no ciphertext, no passphrase
                    }
                )
        out["steps"].append(
            {
                "step": "private_refs",
                "ok": True,
                "shard_count": vs.get("shard_count"),
                "vault": vs.get("vault"),
            }
        )
    except Exception as e:  # noqa: BLE001
        out["steps"].append({"step": "private_refs", "ok": False, "error": str(e)[:160]})

    # --- timeline all axes: t ∥ τ ∥ v (virtual re-enabled, heroic SHU) ---
    timeline_meta: Dict[str, Any] = {}
    if include_timeline:
        try:
            from fusion_hero_os.core.dual_timeline_training import run_auto_train

            # ensure fresh axes (includes virtual heroic samples when enabled)
            tr = run_auto_train(write=True)
            timeline_meta = {
                "files": tr.get("files"),
                "samples": tr.get("samples"),
                "dual_samples": tr.get("dual_samples"),
                "virtual_samples": tr.get("virtual_samples"),
                "virtual_timelines_enabled": tr.get("virtual_timelines_enabled"),
                "heroic_mean": tr.get("heroic_mean"),
                "consistency": tr.get("consistency"),
                "paths": tr.get("paths"),
                "axes": {
                    "t": "real_chronology",
                    "tau": "imaginary_structural_heroic",
                    "v": "virtual_heroic_scenario",
                },
                "platform": PLATFORM,
            }
            out["steps"].append(
                {
                    "step": "dual_virtual_timeline",
                    "ok": bool(tr.get("ok")),
                    "virtual_samples": tr.get("virtual_samples"),
                    "heroic_mean": tr.get("heroic_mean"),
                }
            )
        except Exception as e:  # noqa: BLE001
            out["steps"].append({"step": "dual_virtual_timeline", "ok": False, "error": str(e)[:160]})

    # --- merge links: public identity ↔ private module/function ↔ timeline ---
    for ref in private_refs:
        out["links"].append(
            {
                "public_display_id": public.get("display_id"),
                "public_fingerprint_prefix": (public.get("public_fingerprint") or "")[:16],
                "private_module": ref.get("module"),
                "private_function": ref.get("function"),
                "private_shard_rel": ref.get("shard_rel"),
                "timeline": {
                    "t_range": {
                        "min": (timeline_meta.get("consistency") or {}).get("t_min_iso"),
                        "max": (timeline_meta.get("consistency") or {}).get("t_max_iso"),
                    },
                    "tau_mean": (timeline_meta.get("consistency") or {}).get("tau_mean"),
                    "virtual_samples": timeline_meta.get("virtual_samples"),
                    "heroic_mean": timeline_meta.get("heroic_mean"),
                    "axes": timeline_meta.get("axes"),
                },
                "binding": "merge_both_via_timeline_fusion_musion",
            }
        )

    out["public"] = {
        "display_id": public.get("display_id"),
        "public_fingerprint": public.get("public_fingerprint"),
        "integrity_ok": public.get("integrity_ok"),
    }
    out["private"] = {
        "ref_count": len(private_refs),
        "note": "payloads stay in local GPG shards only",
    }
    out["timeline"] = timeline_meta
    out["ok"] = all(s.get("ok", True) for s in out["steps"])
    out["duration_sec"] = round(time.time() - t0, 2)
    out["ended_at"] = datetime.now(timezone.utc).isoformat()
    out["vocabulary"] = {
        "deploy": "private",
        "push": "public",
        "merge": "both_via_timeline",
    }

    # write merge manifest (local ops — not secrets)
    man_dir = Path.home() / ".fusion" / "ops"
    man_dir.mkdir(parents=True, exist_ok=True)
    man = man_dir / "merge_latest.json"
    man.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    # public-safe summary for docs (no private paths absolute if possible)
    summary = {
        "generated_at": out["ended_at"],
        "operation": "merge",
        "alias": "fusion_musion",
        "meaning": "both_via_timeline",
        "platform": PLATFORM,
        "cycle": "BIG_ALPHA",
        "public_display_id": out["public"].get("display_id"),
        "private_ref_count": out["private"].get("ref_count"),
        "timeline_samples": (timeline_meta or {}).get("samples"),
        "timeline_dual_samples": (timeline_meta or {}).get("dual_samples"),
        "timeline_virtual_samples": (timeline_meta or {}).get("virtual_samples"),
        "virtual_timelines_enabled": (timeline_meta or {}).get("virtual_timelines_enabled"),
        "heroic_mean": (timeline_meta or {}).get("heroic_mean"),
        "timeline_files": (timeline_meta or {}).get("files"),
        "axes": (timeline_meta or {}).get("axes"),
        "link_count": len(out["links"]),
        "ok": out["ok"],
    }
    docs = Path(__file__).resolve().parents[2] / "docs" / "ops"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "merge_latest.summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    out["manifest"] = str(man)
    out["docs_summary"] = str(docs / "merge_latest.summary.json")
    return out


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="merge = both via dual timeline")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--no-deploy", action="store_true")
    ap.add_argument("--no-timeline", action="store_true")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    r = merge_both(run_deploy=not args.no_deploy, include_timeline=not args.no_timeline)
    # compact print
    compact = {
        "ok": r.get("ok"),
        "operation": r.get("operation"),
        "meaning": r.get("meaning"),
        "public_display_id": (r.get("public") or {}).get("display_id"),
        "private_ref_count": (r.get("private") or {}).get("ref_count"),
        "link_count": len(r.get("links") or []),
        "manifest": r.get("manifest"),
        "duration_sec": r.get("duration_sec"),
    }
    print(json.dumps(compact, indent=2, ensure_ascii=False))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
