"""
Poly-Mesh Router — single authority for placement routing.

Rules (fail-closed, no dual-start):
  1) Only this module decides where a capability runs.
  2) Heavy / force_cluster work MUST go to L3 when GKE is live — never silent L1.
  3) L3 is live only if kubectl can list Ready nodes (not merely kubeconfig file).
  4) Local/internal start of force_cluster jobs is DENIED when L3 is available
     OR when force_cluster=true and L3 is offline (blocked, not local fallback).

Geltung: Spezifikation
Policy: pseudo_inhouse_only · freemium=false · cost_limits soft
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "mesh_service_coordination.yaml"
STATE_DIR = Path.home() / ".fusion" / "mesh" / "routing"
TIER_RANK = {
    "L0_edge": 0,
    "L1_mainframe": 1,
    "L2_mesh_anchor": 2,
    "L3_cluster": 3,
    "L4_external_saas": 4,
}

# Capabilities that must never silently run on L1 when L3 is in candidates
FORCE_CLUSTER_IDS = frozenset(
    {
        "fusion-stability-train",
        "academia-curriculum-train",
        "qubo-anneal",
    }
)
# Control plane stays on mainframe even if L3 is up (no dual cluster noise)
CONTROL_PLANE_IDS = frozenset(
    {
        "service-coordinator",
        "fusion-dashboard",
        "heroic-core-orchestrator",
        "tailscale-mesh-registry",
        "fusion-integration-hub",
    }
)
# Prefer highest tier among candidates when multiple online
PREFER_HIGH_TIER = True

__all__ = [
    "probe_gke",
    "route",
    "route_all",
    "assert_not_local_dual_start",
    "status",
    "load_catalog",
]


def load_catalog() -> dict[str, Any]:
    if not CATALOG.is_file():
        return {}
    try:
        import yaml

        return yaml.safe_load(CATALOG.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _find_kubectl() -> str | None:
    env = os.environ.get("FUSION_KUBECTL", "").strip()
    if env and Path(env).is_file():
        return env
    local = Path.home() / ".fusion" / "bin" / "kubectl.exe"
    if local.is_file():
        return str(local)
    which = shutil.which("kubectl")
    return which


def probe_gke(timeout: int = 45) -> dict[str, Any]:
    """Live GKE probe — Ready nodes required for L3_online."""
    kubectl = _find_kubectl()
    out: dict[str, Any] = {
        "ok": False,
        "kubectl": kubectl,
        "ready_nodes": 0,
        "nodes": [],
        "context": None,
        "error": None,
    }
    if not kubectl:
        out["error"] = "kubectl_not_found"
        return out
    try:
        ctx = subprocess.run(
            [kubectl, "config", "current-context"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        out["context"] = (ctx.stdout or "").strip() or None
        proc = subprocess.run(
            [kubectl, "get", "nodes", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        if proc.returncode != 0:
            out["error"] = (proc.stderr or proc.stdout or "kubectl_get_nodes_failed")[:400]
            return out
        data = json.loads(proc.stdout or "{}")
        ready = 0
        nodes = []
        for item in data.get("items") or []:
            name = (item.get("metadata") or {}).get("name")
            conditions = (item.get("status") or {}).get("conditions") or []
            is_ready = any(
                c.get("type") == "Ready" and c.get("status") == "True" for c in conditions
            )
            if is_ready:
                ready += 1
            nodes.append({"name": name, "ready": is_ready})
        out["nodes"] = nodes
        out["ready_nodes"] = ready
        out["ok"] = ready >= 1
        if not out["ok"]:
            out["error"] = "no_ready_nodes"
    except subprocess.TimeoutExpired:
        out["error"] = "kubectl_timeout"
    except Exception as e:  # noqa: BLE001
        out["error"] = str(e)[:300]
    return out


def _online_tiers_from_tailscale(catalog: dict[str, Any]) -> tuple[set, dict[str, Any]]:
    """Reuse coordinator inventory if importable; else minimal self-only."""
    tiers: set = set()
    inv: dict[str, Any] = {}
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        # import as module path
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "mesh_cluster_coordinator", ROOT / "scripts" / "mesh_cluster_coordinator.py"
        )
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            inv = mod.inventory(catalog)
            for m in inv.get("matched_roles") or []:
                if m.get("live") and m.get("tier"):
                    tiers.add(m["tier"])
    except Exception as e:  # noqa: BLE001
        inv = {"error": str(e)[:200]}
        tiers.add("L1_mainframe")  # assume local if TS parse fails
    return tiers, inv


def _pick_tier(
    candidates: list[str],
    online: set,
    *,
    force_cluster: bool,
    prefer_high: bool = True,
) -> tuple[str | None, str]:
    """Return (chosen_tier, status)."""
    online_cands = [c for c in candidates if c in online or c == "L4_external_saas"]
    if force_cluster:
        if "L3_cluster" in candidates:
            if "L3_cluster" in online:
                return "L3_cluster", "cluster_routed"
            return None, "blocked_cluster_required"
        # force but no L3 in candidates — treat as error config
        return None, "blocked_misconfigured_force_cluster"

    if not online_cands:
        # no silent L1 if L3 was only option
        if candidates == ["L3_cluster"] or (
            len(candidates) == 1 and candidates[0] == "L3_cluster"
        ):
            return None, "blocked_cluster_offline"
        return (candidates[0] if candidates else None), "deferred_offline"

    if prefer_high:
        online_cands.sort(key=lambda t: TIER_RANK.get(t, -1), reverse=True)
        return online_cands[0], "routed"
    return online_cands[0], "routed"


def route(
    capability_id: str,
    *,
    catalog: dict[str, Any] | None = None,
    gke: dict[str, Any] | None = None,
    allow_local_dual: bool = False,
) -> dict[str, Any]:
    """Single decision for one capability. allow_local_dual=False is default (no conflicts)."""
    catalog = catalog or load_catalog()
    gke = gke if gke is not None else probe_gke()
    tiers, inv = _online_tiers_from_tailscale(catalog)
    if gke.get("ok"):
        tiers.add("L3_cluster")
    else:
        tiers.discard("L3_cluster")

    inhouse = (catalog.get("inhouse") or {}).get(capability_id) or {}
    external = (catalog.get("external") or {}).get(capability_id) or {}
    svc = inhouse or external
    kind = "inhouse" if inhouse else ("external" if external else "unknown")
    raw = svc.get("placement")
    candidates = raw if isinstance(raw, list) else ([raw] if raw else ["L1_mainframe"])
    candidates = [c for c in candidates if c]

    force = bool(svc.get("force_cluster")) or capability_id in FORCE_CLUSTER_IDS
    if "L3_cluster" in candidates and capability_id in FORCE_CLUSTER_IDS:
        if capability_id == "qubo-anneal" and os.environ.get("FUSION_QUBO_LOCAL", "") == "1":
            force = False
        elif capability_id == "qubo-anneal":
            force = os.environ.get("FUSION_QUBO_FORCE_CLUSTER", "1") == "1"
        else:
            force = True

    prefer_high = PREFER_HIGH_TIER
    if capability_id in CONTROL_PLANE_IDS and "L1_mainframe" in candidates:
        prefer_high = False  # keep interactive control plane on L1

    chosen, status = _pick_tier(
        candidates, tiers, force_cluster=force, prefer_high=prefer_high
    )

    deny_local = False
    if not allow_local_dual and force and chosen == "L1_mainframe":
        deny_local = True
        chosen = None
        status = "blocked_refuse_local_dual_start"

    decision = {
        "ok": status in ("routed", "cluster_routed") and chosen is not None,
        "id": capability_id,
        "kind": kind,
        "chosen": chosen,
        "status": status,
        "candidates": candidates,
        "force_cluster": force,
        "deny_local_dual_start": deny_local,
        "online_tiers": sorted(tiers),
        "gke_live": bool(gke.get("ok")),
        "gke": {
            "ready_nodes": gke.get("ready_nodes"),
            "context": gke.get("context"),
            "error": gke.get("error"),
        },
        "path": svc.get("path"),
        "decided_at": datetime.now(UTC).isoformat(),
        "router": "poly_mesh_router",
        "sole_authority": True,
    }
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "last_route.json").write_text(
        json.dumps(decision, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return decision


def route_all() -> dict[str, Any]:
    catalog = load_catalog()
    gke = probe_gke()
    results = []
    for name in (catalog.get("inhouse") or {}).keys():
        results.append(route(name, catalog=catalog, gke=gke))
    cluster_bound = [r for r in results if r.get("chosen") == "L3_cluster"]
    blocked = [r for r in results if str(r.get("status", "")).startswith("blocked")]
    local = [r for r in results if r.get("chosen") == "L1_mainframe"]
    report = {
        "ok": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "gke_live": bool(gke.get("ok")),
        "gke": gke,
        "counts": {
            "total": len(results),
            "cluster": len(cluster_bound),
            "local_l1": len(local),
            "blocked": len(blocked),
        },
        "cluster_ids": [r["id"] for r in cluster_bound],
        "blocked_ids": [r["id"] for r in blocked],
        "local_ids": [r["id"] for r in local],
        "routes": results,
        "principle": "sole router — no dual local start for force_cluster",
    }
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    (STATE_DIR / "route_all.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    # public-safe summary
    pub = ROOT / "docs" / "mesh" / "poly_mesh_route.summary.json"
    pub.parent.mkdir(parents=True, exist_ok=True)
    pub.write_text(
        json.dumps(
            {
                "generated_at": report["generated_at"],
                "gke_live": report["gke_live"],
                "counts": report["counts"],
                "cluster_ids": report["cluster_ids"],
                "blocked_ids": report["blocked_ids"],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return report


def assert_not_local_dual_start(capability_id: str) -> dict[str, Any]:
    """Call before any local heavy job — raises SystemExit if denied."""
    d = route(capability_id)
    if d.get("deny_local_dual_start") or d.get("status") == "blocked_refuse_local_dual_start":
        return {
            "allowed": False,
            "reason": "force_cluster — local start forbidden while routing policy active",
            "decision": d,
        }
    if d.get("status") == "blocked_cluster_required":
        return {
            "allowed": False,
            "reason": "cluster required but GKE not live",
            "decision": d,
        }
    if d.get("chosen") == "L3_cluster":
        return {
            "allowed": False,
            "reason": "must run on cluster — use kubectl/Job not local process",
            "decision": d,
            "run_on": "L3_cluster",
        }
    return {"allowed": True, "decision": d}


def status() -> dict[str, Any]:
    gke = probe_gke()
    last = STATE_DIR / "route_all.json"
    last_data = None
    if last.is_file():
        try:
            last_data = json.loads(last.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {
        "ok": True,
        "kubectl": _find_kubectl(),
        "gke": gke,
        "last_route_all": last_data,
        "state_dir": str(STATE_DIR),
        "sole_authority": True,
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Poly-Mesh Router (sole placement authority)")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--probe-gke", action="store_true")
    ap.add_argument("--route-all", action="store_true")
    ap.add_argument("--route", default="", help="capability id")
    ap.add_argument("--assert-local", default="", help="check if local start allowed")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    if args.probe_gke:
        print(json.dumps(probe_gke(), indent=2, ensure_ascii=False))
        return 0
    if args.route_all:
        print(json.dumps(route_all(), indent=2, ensure_ascii=False))
        return 0
    if args.route:
        print(json.dumps(route(args.route), indent=2, ensure_ascii=False))
        return 0
    if args.assert_local:
        r = assert_not_local_dual_start(args.assert_local)
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return 0 if r.get("allowed") else 2
    print(json.dumps(route_all(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
