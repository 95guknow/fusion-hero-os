"""Poly-Mesh Algorithm Orchestrator — perfect placement + dispatch (v10).

Sole placement authority remains ``poly_mesh_router``. This module:
  1) Probes live mesh (Tailscale + GKE)
  2) Routes every algorithm/capability
  3) Builds an executable orchestration plan (no dual-start)
  4) Optionally dispatches allowed actions (coordinator, L3 hooks, L1 control)
  5) Scores coherence (perfect = 100 when policy holds)

Algorithms are catalog inhouse IDs + OS organs from mesh_os_port.

Geltung: Spezifikation · live topology = empirical.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

__all__ = [
    "orchestrate",
    "plan_only",
    "coherence_score",
    "status",
]

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = Path.home() / ".fusion" / "mesh" / "orchestration"
PLAN_PATH = STATE_DIR / "last_plan.json"
REPORT_PATH = STATE_DIR / "last_report.json"

# Algorithm classes for perfect orchestration
ALGO_CLASS = {
    "qubo-anneal": "force_cluster_compute",
    "fusion-stability-train": "force_cluster_compute",
    "academia-curriculum-train": "force_cluster_compute",
    "dependency-atlas": "force_cluster_compute",
    "service-coordinator": "control_plane",
    "fusion-dashboard": "control_plane",
    "heroic-core-orchestrator": "control_plane",
    "tailscale-mesh-registry": "control_plane",
    "fusion-integration-hub": "control_plane",
    "hyperthreading-engine": "control_plane",
    "fractal-mainframe-mesh": "mesh_replica",
    "headset-relay": "edge_audio",
    "comaedchen-audio": "edge_audio",
}


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _load_router():
    from fusion_hero_os.core.poly_mesh_router import (
        assert_not_local_dual_start,
        load_catalog,
        probe_gke,
        route,
        route_all,
    )

    return {
        "load_catalog": load_catalog,
        "probe_gke": probe_gke,
        "route": route,
        "route_all": route_all,
        "assert_not_local_dual_start": assert_not_local_dual_start,
    }


def _mesh_inventory() -> dict[str, Any]:
    try:
        from fusion_hero_os.core.poly_mesh_os_port import inventory_mesh

        return inventory_mesh()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200], "tiers_online": ["L1_mainframe"]}


def _algo_class(cap_id: str, route_dec: dict[str, Any]) -> str:
    if cap_id in ALGO_CLASS:
        return ALGO_CLASS[cap_id]
    if route_dec.get("force_cluster"):
        return "force_cluster_compute"
    if route_dec.get("chosen") == "L1_mainframe":
        return "control_plane"
    if route_dec.get("chosen") == "L2_mesh_anchor":
        return "mesh_replica"
    if route_dec.get("chosen") == "L3_cluster":
        return "force_cluster_compute"
    if route_dec.get("chosen") == "L0_edge":
        return "edge_audio"
    return "general"


def _dispatch_action(route_dec: dict[str, Any], algo_class: str) -> dict[str, Any]:
    """Decide what orchestration would DO (execute or dry)."""
    status = route_dec.get("status")
    chosen = route_dec.get("chosen")
    cid = route_dec.get("id")
    if str(status).startswith("blocked"):
        return {
            "action": "block",
            "reason": status,
            "execute": False,
            "message": f"{cid}: blocked ({status}) — no local dual-start",
        }
    if chosen == "L3_cluster":
        return {
            "action": "cluster_job",
            "reason": "force_cluster_or_high_tier",
            "execute": False,  # kubectl submit is explicit hook
            "message": f"{cid}: schedule on L3 GKE (Job/Cron) — not local process",
            "hook": "kubectl apply -f infra/k8s/fusion-training/ or coordination cron",
        }
    if chosen == "L1_mainframe":
        if algo_class == "control_plane":
            return {
                "action": "run_l1_control",
                "reason": "control_plane_affinity",
                "execute": True,
                "message": f"{cid}: L1 control plane (dashboard/MCP/orchestrator)",
            }
        return {
            "action": "run_l1",
            "reason": "routed_l1",
            "execute": True,
            "message": f"{cid}: L1 allowed",
        }
    if chosen == "L2_mesh_anchor":
        return {
            "action": "run_l2_exit",
            "reason": "mesh_replica",
            "execute": False,
            "message": f"{cid}: prefer fusion-mesh-exit always-on",
            "hook": "ssh/mesh_join or fractal replicate on L2",
        }
    if chosen == "L0_edge":
        return {
            "action": "edge_client",
            "reason": "phone_edge",
            "execute": False,
            "message": f"{cid}: phone client (AudioRelay mesh-only)",
            "hook": "force-headset-mesh-only + phone connect 100.x",
        }
    if chosen == "L4_external_saas":
        return {
            "action": "saas_membrane",
            "reason": "external",
            "execute": False,
            "message": f"{cid}: L4 SaaS via L1 MCP — never source of truth",
        }
    return {
        "action": "defer",
        "reason": status or "unknown",
        "execute": False,
        "message": f"{cid}: deferred",
    }


def coherence_score(plan: dict[str, Any]) -> dict[str, Any]:
    """0–100: perfect orchestration when policy invariants hold."""
    routes = plan.get("algorithms") or []
    if not routes:
        return {"score": 0, "grade": "empty", "checks": {}}

    checks = {
        "sole_authority": plan.get("sole_authority") == "poly_mesh_router",
        "no_dual_start": True,
        "force_cluster_on_l3_or_blocked": True,
        "control_plane_on_l1": True,
        "has_online_tiers": bool(plan.get("online_tiers")),
        "mesh_inventory_ok": bool((plan.get("mesh") or {}).get("ok")),
    }
    violations: list[str] = []

    for r in routes:
        st = r.get("status") or ""
        chosen = r.get("chosen")
        force = r.get("force_cluster")
        algo = r.get("algo_class")
        if force and chosen == "L1_mainframe":
            checks["no_dual_start"] = False
            checks["force_cluster_on_l3_or_blocked"] = False
            violations.append(f"{r.get('id')}: force_cluster on L1")
        if force and chosen not in (None, "L3_cluster") and not str(st).startswith("blocked"):
            if chosen != "L3_cluster":
                checks["force_cluster_on_l3_or_blocked"] = False
                violations.append(f"{r.get('id')}: force not L3 ({chosen})")
        if algo == "control_plane" and chosen not in (None, "L1_mainframe") and chosen != "L1_mainframe":
            # control plane preferred L1 — warn if elsewhere unless blocked
            if chosen and chosen != "L1_mainframe":
                checks["control_plane_on_l1"] = False
                violations.append(f"{r.get('id')}: control plane on {chosen}")

    # dual-start blocked statuses are good
    for r in routes:
        if r.get("deny_local_dual_start"):
            checks["no_dual_start"] = checks["no_dual_start"] and True

    weights = {
        "sole_authority": 20,
        "no_dual_start": 25,
        "force_cluster_on_l3_or_blocked": 25,
        "control_plane_on_l1": 15,
        "has_online_tiers": 10,
        "mesh_inventory_ok": 5,
    }
    score = sum(weights[k] for k, ok in checks.items() if ok)
    grade = (
        "perfect"
        if score >= 100
        else "excellent"
        if score >= 90
        else "good"
        if score >= 75
        else "degraded"
        if score >= 50
        else "broken"
    )
    return {
        "score": score,
        "grade": grade,
        "checks": checks,
        "violations": violations,
        "perfect": score >= 100 and not violations,
    }


def plan_only() -> dict[str, Any]:
    """Build full orchestration plan without side effects."""
    R = _load_router()
    gke = R["probe_gke"]()
    mesh = _mesh_inventory()
    routed = R["route_all"]()

    online = set()
    for r in routed.get("routes") or []:
        for t in r.get("online_tiers") or []:
            online.add(t)
    if gke.get("ok"):
        online.add("L3_cluster")
    for t in mesh.get("tiers_online") or []:
        online.add(t)

    algorithms: list[dict[str, Any]] = []
    for r in routed.get("routes") or []:
        algo = _algo_class(r.get("id") or "", r)
        disp = _dispatch_action(r, algo)
        algorithms.append(
            {
                **{k: r.get(k) for k in (
                    "id", "kind", "chosen", "status", "candidates",
                    "force_cluster", "deny_local_dual_start", "path", "ok",
                )},
                "algo_class": algo,
                "dispatch": disp,
            }
        )

    # OS organs as soft placement (from port registry if present)
    organs = []
    try:
        from fusion_hero_os.core.poly_mesh_os_port import build_port_registry

        reg = build_port_registry(mesh)
        for o in reg.get("organs") or []:
            organs.append(
                {
                    "id": o.get("id"),
                    "placement": o.get("placement"),
                    "plane": o.get("plane"),
                    "mesh_url": o.get("mesh_url"),
                    "tier_online": o.get("tier_online"),
                    "algo_class": "os_organ",
                }
            )
    except Exception as exc:  # noqa: BLE001
        organs = [{"error": str(exc)[:160]}]

    plan = {
        "ok": True,
        "generated_at": _now(),
        "platform_version": "10.0.0",
        "sole_authority": "poly_mesh_router",
        "orchestrator": "poly_mesh_orchestrator",
        "online_tiers": sorted(online),
        "gke_live": bool(gke.get("ok")),
        "gke": {
            "ready_nodes": gke.get("ready_nodes"),
            "context": gke.get("context"),
            "error": gke.get("error"),
        },
        "mesh": {
            "ok": mesh.get("ok"),
            "self": mesh.get("self"),
            "tiers_online": mesh.get("tiers_online"),
            "peer_count": len(mesh.get("peers") or []),
        },
        "counts": routed.get("counts") or {},
        "algorithms": algorithms,
        "organs": organs,
        "waves": _build_waves(algorithms),
        "policy": {
            "no_dual_start": True,
            "force_cluster_to_l3": True,
            "control_plane_l1": True,
            "audio_mesh_only": True,
            "saas_not_source_of_truth": True,
        },
    }
    plan["coherence"] = coherence_score(plan)
    plan["banner"] = (
        f"POLY-MESH ORCHESTRATION | score={plan['coherence']['score']} "
        f"grade={plan['coherence']['grade']} | "
        f"tiers={','.join(plan['online_tiers'])} | "
        f"algos={len(algorithms)} | "
        f"cluster={plan['counts'].get('cluster', 0)} "
        f"blocked={plan['counts'].get('blocked', 0)} "
        f"l1={plan['counts'].get('local_l1', 0)}"
    )
    return plan


def _build_waves(algorithms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Ordered execution waves for perfect orchestration."""
    waves = [
        {
            "wave": 0,
            "name": "control_plane_l1",
            "ids": [
                a["id"]
                for a in algorithms
                if a.get("algo_class") == "control_plane" and a.get("chosen") == "L1_mainframe"
            ],
        },
        {
            "wave": 1,
            "name": "mesh_replica_l2",
            "ids": [
                a["id"]
                for a in algorithms
                if a.get("chosen") == "L2_mesh_anchor"
            ],
        },
        {
            "wave": 2,
            "name": "force_cluster_l3",
            "ids": [
                a["id"]
                for a in algorithms
                if a.get("chosen") == "L3_cluster" or (
                    a.get("force_cluster") and str(a.get("status", "")).startswith("blocked")
                )
            ],
        },
        {
            "wave": 3,
            "name": "edge_audio_l0",
            "ids": [
                a["id"]
                for a in algorithms
                if a.get("algo_class") == "edge_audio" or a.get("chosen") == "L0_edge"
            ],
        },
        {
            "wave": 4,
            "name": "general_routed",
            "ids": [
                a["id"]
                for a in algorithms
                if a.get("ok")
                and a.get("algo_class") not in (
                    "control_plane",
                    "force_cluster_compute",
                    "edge_audio",
                    "mesh_replica",
                )
            ],
        },
    ]
    return waves


def _execute_hooks(plan: dict[str, Any], *, execute: bool) -> dict[str, Any]:
    """Run safe orchestration hooks when execute=True."""
    steps: dict[str, Any] = {}
    if not execute:
        steps["mode"] = "dry_run"
        steps["note"] = "Pass execute=True to run coordinator + dual-start asserts"
        return steps

    steps["mode"] = "execute"
    # 1) Coordinator inventory+plan
    try:
        r = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "mesh_cluster_coordinator.py"), "--mode", "all"],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(ROOT),
        )
        steps["coordinator"] = {
            "ok": r.returncode == 0,
            "rc": r.returncode,
            "stdout_tail": (r.stdout or "")[-300:],
        }
    except Exception as exc:  # noqa: BLE001
        steps["coordinator"] = {"ok": False, "error": str(exc)[:200]}

    # 2) Dual-start asserts for force_cluster algos
    R = _load_router()
    asserts = []
    for a in plan.get("algorithms") or []:
        if not a.get("force_cluster"):
            continue
        res = R["assert_not_local_dual_start"](a["id"])
        asserts.append({"id": a["id"], **{k: res.get(k) for k in ("allowed", "reason", "run_on")}})
    steps["dual_start_asserts"] = asserts

    # 3) Headset mesh_only
    try:
        from fusion_hero_os.core.headset_layers import set_mesh_only, status as hs

        set_mesh_only(True)
        st = hs(apply_probe=False)
        steps["headset"] = {
            "ok": True,
            "mesh_only": st.get("mesh_only"),
            "active": st.get("active"),
            "connected_to_phone": st.get("connected_to_phone"),
            "mesh_link_ok": st.get("mesh_link_ok"),
            "lan_violation": st.get("lan_violation"),
        }
    except Exception as exc:  # noqa: BLE001
        steps["headset"] = {"ok": False, "error": str(exc)[:160]}

    # 4) OS port refresh (no serve by default)
    try:
        from fusion_hero_os.core.poly_mesh_os_port import port_os

        pr = port_os(serve=False, run_coordinator=False)
        steps["os_port"] = {
            "ok": pr.get("ok"),
            "organ_count": pr.get("organ_count"),
            "mesh_ip": (pr.get("inventory") or {}).get("self", {}).get("mesh_ip"),
        }
    except Exception as exc:  # noqa: BLE001
        steps["os_port"] = {"ok": False, "error": str(exc)[:160]}

    return steps


def orchestrate(*, execute: bool = False) -> dict[str, Any]:
    """Perfect poly-mesh algorithm orchestration plan (+ optional execute)."""
    plan = plan_only()
    steps = _execute_hooks(plan, execute=execute)
    # re-score after execute side effects still uses same plan topology
    report = {
        **plan,
        "execute": execute,
        "steps": steps,
        "coherence": coherence_score(plan),
    }
    report["banner"] = (
        f"POLY-MESH ORCHESTRATION | score={report['coherence']['score']} "
        f"grade={report['coherence']['grade']} "
        f"perfect={report['coherence']['perfect']} | "
        f"execute={execute} | tiers={','.join(report.get('online_tiers') or [])}"
    )

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PLAN_PATH.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    REPORT_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    # public summary
    pub = ROOT / "docs" / "mesh" / "poly_mesh_orchestration.summary.json"
    pub.parent.mkdir(parents=True, exist_ok=True)
    pub.write_text(
        json.dumps(
            {
                "generated_at": report["generated_at"],
                "score": report["coherence"]["score"],
                "grade": report["coherence"]["grade"],
                "perfect": report["coherence"]["perfect"],
                "online_tiers": report["online_tiers"],
                "counts": report["counts"],
                "waves": [
                    {"wave": w["wave"], "name": w["name"], "n": len(w["ids"])}
                    for w in report.get("waves") or []
                ],
                "violations": report["coherence"].get("violations") or [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return report


def status() -> dict[str, Any]:
    out: dict[str, Any] = {
        "ok": True,
        "state_dir": str(STATE_DIR),
        "has_plan": PLAN_PATH.is_file(),
        "has_report": REPORT_PATH.is_file(),
    }
    if REPORT_PATH.is_file():
        try:
            rep = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
            out["last"] = {
                "generated_at": rep.get("generated_at"),
                "score": (rep.get("coherence") or {}).get("score"),
                "grade": (rep.get("coherence") or {}).get("grade"),
                "banner": rep.get("banner"),
                "online_tiers": rep.get("online_tiers"),
            }
        except Exception:
            pass
    return out


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Poly-Mesh Algorithm Orchestrator")
    ap.add_argument("--plan", action="store_true", help="plan only")
    ap.add_argument("--execute", action="store_true", help="plan + run hooks")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.status:
        r = status()
    elif args.execute:
        r = orchestrate(execute=True)
    else:
        r = orchestrate(execute=False) if not args.plan else plan_only()
        if args.plan and "coherence" not in r:
            r["coherence"] = coherence_score(r)

    print(json.dumps(r, indent=2, ensure_ascii=False))
    if r.get("banner"):
        print(r["banner"], file=sys.stderr)
    coh = r.get("coherence") or {}
    if coh.get("perfect"):
        return 0
    if coh.get("score", 0) >= 75:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
