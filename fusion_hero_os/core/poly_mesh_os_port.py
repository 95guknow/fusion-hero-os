"""Poly-Mesh OS Port — register Fusion Hero OS organs on the mesh fabric.

Ports the OS into L0–L4 poly-mesh placement (Tailscale + GKE + exit), without
moving secrets off L1. Writes operator-local registry under
``~/.fusion/mesh/os_port/``.

Geltung: Spezifikation (port membrane) · live topology = empirical.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any

__all__ = [
    "load_manifest",
    "inventory_mesh",
    "build_port_registry",
    "port_status",
    "try_mesh_serve_dashboard",
    "port_os",
]

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "mesh_os_port.yaml"
OUT_DIR = Path.home() / ".fusion" / "mesh" / "os_port"
REGISTRY = OUT_DIR / "registry.json"
LATEST = OUT_DIR / "latest.json"
TS = Path(r"C:\Program Files\Tailscale\tailscale.exe")


def _now() -> str:
    return datetime.now(UTC).isoformat()


def load_manifest() -> dict[str, Any]:
    path = Path(os.environ.get("FUSION_MESH_OS_PORT", str(MANIFEST)))
    if not path.is_file():
        return {"version": "missing", "organs": {}}
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        return data if isinstance(data, dict) else {}
    except Exception as exc:  # noqa: BLE001
        return {"version": "error", "error": str(exc)[:200], "organs": {}}


def _ts_json() -> dict[str, Any]:
    exe = str(TS) if TS.is_file() else "tailscale"
    try:
        r = subprocess.run(
            [exe, "status", "--json"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return {"ok": False, "error": "tailscale_status_failed"}
        return {"ok": True, "data": json.loads(r.stdout)}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def inventory_mesh() -> dict[str, Any]:
    """Live Tailscale inventory + tier hints."""
    raw = _ts_json()
    out: dict[str, Any] = {
        "ok": bool(raw.get("ok")),
        "ts": _now(),
        "self": {},
        "peers": [],
        "tiers_online": [],
        "error": raw.get("error"),
    }
    if not raw.get("ok"):
        return out
    data = raw["data"]
    self_n = data.get("Self") or {}
    self_host = (self_n.get("HostName") or self_n.get("DNSName") or "").rstrip(".")
    self_ips = list(self_n.get("TailscaleIPs") or [])
    out["self"] = {
        "hostname": self_host,
        "online": bool(self_n.get("Online", True)),
        "ips": self_ips,
        "mesh_ip": next((i for i in self_ips if str(i).startswith("100.")), self_ips[0] if self_ips else None),
        "os": self_n.get("OS"),
        "tier_hint": _tier_for_host(self_host),
    }
    peers = []
    for _id, p in (data.get("Peer") or {}).items():
        if not isinstance(p, dict):
            continue
        host = (p.get("HostName") or p.get("DNSName") or "").rstrip(".")
        ips = list(p.get("TailscaleIPs") or [])
        peers.append(
            {
                "hostname": host,
                "online": bool(p.get("Online")),
                "ips": ips,
                "mesh_ip": next((i for i in ips if str(i).startswith("100.")), ips[0] if ips else None),
                "os": p.get("OS"),
                "exit_node": bool(p.get("ExitNode")),
                "tier_hint": _tier_for_host(host),
            }
        )
    out["peers"] = peers

    # tiers
    tiers = set()
    if out["self"].get("online"):
        tiers.add(out["self"].get("tier_hint") or "L1_mainframe")
    for p in peers:
        if p.get("online") and p.get("tier_hint"):
            tiers.add(p["tier_hint"])
    # GKE soft probe
    try:
        from fusion_hero_os.core.poly_mesh_router import probe_gke

        gke = probe_gke()
        if gke.get("ok"):
            tiers.add("L3_cluster")
        out["gke"] = {
            "ok": bool(gke.get("ok")),
            "ready_nodes": gke.get("ready_nodes"),
            "error": gke.get("error"),
        }
    except Exception as exc:  # noqa: BLE001
        out["gke"] = {"ok": False, "error": str(exc)[:120]}

    out["tiers_online"] = sorted(t for t in tiers if t)
    return out


def _tier_for_host(hostname: str) -> str:
    h = (hostname or "").lower()
    if any(x in h for x in ("redmi", "phone")):
        return "L0_edge"
    if any(x in h for x in ("mesh-exit", "fusion-mesh-exit", "exit")):
        return "L2_mesh_anchor"
    if "subnet-router" in h or "tailscale-subnet" in h:
        return "L2_mesh_anchor"
    if h.startswith("cs-") or "cloudshell" in h:
        return "ephemeral"
    if any(x in h for x in ("desktop", "mainframe", "kpki")):
        return "L1_mainframe"
    return "L1_mainframe"


def build_port_registry(inv: dict[str, Any] | None = None) -> dict[str, Any]:
    """Bind manifest organs to live mesh addresses."""
    inv = inv or inventory_mesh()
    man = load_manifest()
    self_ip = (inv.get("self") or {}).get("mesh_ip")
    self_host = (inv.get("self") or {}).get("hostname")
    organs_out = []
    for oid, meta in (man.get("organs") or {}).items():
        if not isinstance(meta, dict):
            continue
        placement = meta.get("placement") or "L1_mainframe"
        entry: dict[str, Any] = {
            "id": oid,
            "placement": placement,
            "plane": meta.get("plane"),
            "description": meta.get("description"),
            "local_url": meta.get("local_url"),
            "mesh_path": meta.get("mesh_path"),
            "local_only": bool(meta.get("local_only")),
            "mesh_serve": bool(meta.get("mesh_serve")),
            "mesh_only_required": bool(meta.get("mesh_only_required")),
        }
        if self_ip and meta.get("mesh_path") and not meta.get("local_only"):
            path = meta.get("mesh_path") or "/"
            entry["mesh_url"] = f"http://{self_ip}:8000{path}"
            if self_host:
                entry["mesh_magic_hint"] = f"http://{self_host}:8000{path}"
        if meta.get("gke_cron"):
            entry["gke_cron"] = meta["gke_cron"]
        if meta.get("gcs_prefix"):
            entry["gcs_prefix"] = meta["gcs_prefix"]
        # tier online?
        entry["tier_online"] = placement in (inv.get("tiers_online") or [])
        organs_out.append(entry)

    return {
        "ok": True,
        "version": man.get("version"),
        "platform_version": man.get("platform_version", "10.0.0"),
        "ported_at": _now(),
        "principle": man.get("principle"),
        "transport": man.get("transport"),
        "inventory": {
            "self": inv.get("self"),
            "peers": inv.get("peers"),
            "tiers_online": inv.get("tiers_online"),
            "gke": inv.get("gke"),
        },
        "organs": organs_out,
        "placement_rules": man.get("placement_rules") or [],
        "anti_patterns": man.get("anti_patterns") or [],
        "entrypoints": {
            "status": "python -m fusion_hero_os.core.poly_mesh_os_port --status",
            "port": "python scripts/port_os_poly_mesh.py",
            "coordinator": "python scripts/mesh_cluster_coordinator.py --mode all",
        },
    }


def try_mesh_serve_dashboard(port: int = 8000) -> dict[str, Any]:
    """Advertise local dashboard on Tailscale serve (mesh-visible, not Funnel)."""
    exe = str(TS) if TS.is_file() else "tailscale"
    # Prefer modern: tailscale serve --bg 8000
    attempts = [
        [exe, "serve", "--bg", str(port)],
        [exe, "serve", "https", "/", f"http://127.0.0.1:{port}"],
        [exe, "serve", "http", "/", f"http://127.0.0.1:{port}"],
    ]
    last: dict[str, Any] = {"ok": False}
    for cmd in attempts:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            last = {
                "ok": r.returncode == 0,
                "cmd": " ".join(cmd),
                "stdout": (r.stdout or "")[:400],
                "stderr": (r.stderr or "")[:400],
                "rc": r.returncode,
            }
            if r.returncode == 0:
                break
        except Exception as exc:  # noqa: BLE001
            last = {"ok": False, "error": str(exc)[:200], "cmd": " ".join(cmd)}
    # status
    try:
        r2 = subprocess.run(
            [exe, "serve", "status"],
            capture_output=True,
            text=True,
            timeout=15,
        )
        last["serve_status"] = (r2.stdout or r2.stderr or "")[:600]
    except Exception:
        pass
    return last


def port_status() -> dict[str, Any]:
    if LATEST.is_file():
        try:
            reg = json.loads(LATEST.read_text(encoding="utf-8"))
        except Exception:
            reg = build_port_registry()
    else:
        reg = build_port_registry()
    inv = inventory_mesh()
    return {
        "ok": True,
        "ported": LATEST.is_file(),
        "registry_path": str(LATEST),
        "self": inv.get("self"),
        "tiers_online": inv.get("tiers_online"),
        "organ_count": len(reg.get("organs") or []),
        "organs_summary": [
            {
                "id": o.get("id"),
                "placement": o.get("placement"),
                "plane": o.get("plane"),
                "mesh_url": o.get("mesh_url"),
                "tier_online": o.get("tier_online"),
            }
            for o in (reg.get("organs") or [])
        ],
        "serve_hint": "tailscale serve --bg 8000  # after dashboard up",
    }


def port_os(*, serve: bool = True, run_coordinator: bool = True) -> dict[str, Any]:
    """Full port: inventory → registry → optional serve → optional coordinator."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    inv = inventory_mesh()
    reg = build_port_registry(inv)
    REGISTRY.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")
    LATEST.write_text(json.dumps(reg, indent=2, ensure_ascii=False), encoding="utf-8")

    report: dict[str, Any] = {
        "ok": bool(inv.get("ok")),
        "action": "port_os_poly_mesh",
        "ts": _now(),
        "platform_version": "10.0.0",
        "registry": str(LATEST),
        "inventory": {
            "self": inv.get("self"),
            "tiers_online": inv.get("tiers_online"),
            "peer_count": len(inv.get("peers") or []),
        },
        "organ_count": len(reg.get("organs") or []),
        "steps": {},
    }

    if serve:
        report["steps"]["mesh_serve"] = try_mesh_serve_dashboard(8000)
    else:
        report["steps"]["mesh_serve"] = {"ok": True, "skipped": True}

    if run_coordinator:
        try:
            r = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "mesh_cluster_coordinator.py"), "--mode", "all"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(ROOT),
            )
            report["steps"]["coordinator"] = {
                "ok": r.returncode == 0,
                "rc": r.returncode,
                "stdout_tail": (r.stdout or "")[-400:],
            }
        except Exception as exc:  # noqa: BLE001
            report["steps"]["coordinator"] = {"ok": False, "error": str(exc)[:200]}

    # mesh_only headset flag
    try:
        from fusion_hero_os.core.headset_layers import set_mesh_only

        set_mesh_only(True)
        report["steps"]["headset_mesh_only"] = {"ok": True, "mesh_only": True}
    except Exception as exc:  # noqa: BLE001
        report["steps"]["headset_mesh_only"] = {"ok": False, "error": str(exc)[:120]}

    # operator public view (no legal name)
    try:
        from fusion_hero_os.core.operator_identity import public_operator_view

        report["operator"] = public_operator_view()
    except Exception:
        report["operator"] = {"role": "operator"}

    report["mesh_urls"] = [
        o.get("mesh_url") for o in (reg.get("organs") or []) if o.get("mesh_url")
    ]
    report["banner"] = (
        f"OS PORTED TO POLY-MESH | self={ (inv.get('self') or {}).get('mesh_ip') } "
        f"| tiers={','.join(inv.get('tiers_online') or [])} "
        f"| organs={len(reg.get('organs') or [])}"
    )
    (OUT_DIR / "port_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Poly-Mesh OS Port")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--port", action="store_true", help="run full port")
    ap.add_argument("--no-serve", action="store_true")
    ap.add_argument("--no-coordinator", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.port:
        r = port_os(serve=not args.no_serve, run_coordinator=not args.no_coordinator)
    else:
        r = port_status() if args.status else port_status()

    if args.json or True:
        print(json.dumps(r, indent=2, ensure_ascii=False))
    if r.get("banner"):
        print(r["banner"], file=sys.stderr)
    return 0 if r.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
