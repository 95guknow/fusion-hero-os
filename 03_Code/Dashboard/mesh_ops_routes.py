# -*- coding: utf-8 -*-
"""Mesh Ops API — unified poly-mesh + Tailscale + entwicklungsquant surface (P1)."""
from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query

router = APIRouter(tags=["mesh-ops"])


def _ts_exe() -> Optional[str]:
    candidates = [
        r"C:\Program Files\Tailscale\tailscale.exe",
        "tailscale",
    ]
    for c in candidates:
        if Path(c).is_file() or shutil.which(c):
            return c if Path(c).is_file() else shutil.which(c)
    return None


def _tailscale_status() -> Dict[str, Any]:
    exe = _ts_exe()
    if not exe:
        return {"ok": False, "error": "tailscale CLI not found"}
    try:
        raw = subprocess.check_output(
            [exe, "status", "--json"],
            timeout=12,
            stderr=subprocess.DEVNULL,
        )
        data = json.loads(raw.decode("utf-8", errors="replace"))
        self = data.get("Self") or {}
        peers = data.get("Peer") or {}
        online = sum(1 for p in peers.values() if p.get("Online"))
        return {
            "ok": True,
            "backend": data.get("BackendState"),
            "self": {
                "hostname": self.get("HostName"),
                "ips": self.get("TailscaleIPs"),
                "online": self.get("Online"),
                "dns": self.get("DNSName"),
            },
            "peer_count": len(peers),
            "peers_online": online,
            "magic_dns": (data.get("CurrentTailnet") or {}).get("MagicDNSSuffix"),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def _funnel_status() -> Dict[str, Any]:
    exe = _ts_exe()
    if not exe:
        return {"ok": False, "error": "tailscale CLI not found"}
    try:
        raw = subprocess.check_output(
            [exe, "funnel", "status", "--json"],
            timeout=10,
            stderr=subprocess.DEVNULL,
        )
        return {"ok": True, "config": json.loads(raw.decode("utf-8", errors="replace"))}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:160]}


def _poly_mesh() -> Dict[str, Any]:
    out: Dict[str, Any] = {"ok": True}
    try:
        from fusion_hero_os.core.poly_mesh_router import probe_gke

        out["gke"] = probe_gke()
    except Exception as exc:  # noqa: BLE001
        out["gke"] = {"ok": False, "error": str(exc)[:160]}
    try:
        from fusion_hero_os.core import poly_mesh_os_port as port

        if hasattr(port, "status"):
            out["os_port"] = port.status()
        elif hasattr(port, "port_status"):
            out["os_port"] = port.port_status()
        else:
            out["os_port"] = {"ok": True, "module": "poly_mesh_os_port"}
    except Exception as exc:  # noqa: BLE001
        out["os_port"] = {"ok": False, "error": str(exc)[:160]}
    try:
        from fusion_hero_os.core.poly_mesh_cost_function import cost_function_status

        out["cost"] = cost_function_status()
    except Exception as exc:  # noqa: BLE001
        out["cost"] = {"ok": False, "error": str(exc)[:120]}
    return out


def _entwicklungsquant_status() -> Dict[str, Any]:
    import sys
    from pathlib import Path

    code = Path(__file__).resolve().parents[1] / "core"
    if str(code) not in sys.path:
        sys.path.insert(0, str(code.parent))
        sys.path.insert(0, str(code))
    try:
        from entwicklungsquant_bus import EntwicklungsquantBus  # type: ignore

        bus = EntwicklungsquantBus()
        if hasattr(bus, "status") and callable(bus.status):
            return {"ok": True, "bus": bus.status()}
        return {
            "ok": True,
            "available": True,
            "class": type(bus).__name__,
            "note": "Bus importable",
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def _registry_stubs_cleared() -> Dict[str, Any]:
    try:
        from fusion_hero_os.registry import Registry

        reg = Registry()
        names = [
            "modules.mainframe_laden",
            "modules.builder_profile",
            "modules.skill_creator",
        ]
        out = {}
        for n in names:
            spec = reg.load(n)
            out[n] = {
                "status": spec.status.value,
                "stub_flag": spec.stub,
                "error": spec.error,
            }
        return {"ok": True, "modules": out}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


def _quantize_selfmod_status() -> Dict[str, Any]:
    try:
        from fusion_hero_os.core.tailscale_quantize_selfmod import status

        return status()
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)[:200]}


@router.get("/api/mesh/ops")
async def mesh_ops_root() -> Dict[str, Any]:
    """Unified mesh ops snapshot (poly-mesh + tailscale + quant bus + P1 stubs)."""
    ts, funnel, poly, quant, stubs, qsm = await asyncio.gather(
        asyncio.to_thread(_tailscale_status),
        asyncio.to_thread(_funnel_status),
        asyncio.to_thread(_poly_mesh),
        asyncio.to_thread(_entwicklungsquant_status),
        asyncio.to_thread(_registry_stubs_cleared),
        asyncio.to_thread(_quantize_selfmod_status),
    )
    return {
        "ok": True,
        "platform_version": "12.0.0",
        "plane": "hyperraum",
        "tailscale": ts,
        "funnel": funnel,
        "poly_mesh": poly,
        "entwicklungsquant": quant,
        "quantize_selfmod": qsm,
        "p1_wiring": stubs,
        "endpoints": {
            "tailscale": "/api/mesh/ops/tailscale",
            "funnel": "/api/mesh/ops/funnel",
            "poly": "/api/mesh/ops/poly",
            "quant": "/api/mesh/ops/entwicklungsquant",
            "quantize_selfmod": "/api/mesh/ops/quantize-selfmod",
            "quantize_selfmod_cycle": "/api/mesh/ops/quantize-selfmod/cycle",
            "p1": "/api/mesh/ops/p1",
        },
    }


@router.get("/api/mesh/ops/tailscale")
async def mesh_ops_tailscale() -> Dict[str, Any]:
    return await asyncio.to_thread(_tailscale_status)


@router.get("/api/mesh/ops/funnel")
async def mesh_ops_funnel() -> Dict[str, Any]:
    return await asyncio.to_thread(_funnel_status)


@router.get("/api/mesh/ops/poly")
async def mesh_ops_poly() -> Dict[str, Any]:
    return await asyncio.to_thread(_poly_mesh)


@router.get("/api/mesh/ops/entwicklungsquant")
async def mesh_ops_quant() -> Dict[str, Any]:
    return await asyncio.to_thread(_entwicklungsquant_status)


@router.get("/api/mesh/ops/quantize-selfmod")
async def mesh_ops_quantize_selfmod() -> Dict[str, Any]:
    """Tailscale-assisted self-modulating quantization status."""
    return await asyncio.to_thread(_quantize_selfmod_status)


@router.post("/api/mesh/ops/quantize-selfmod/ensure")
async def mesh_ops_quantize_selfmod_ensure() -> Dict[str, Any]:
    def _run():
        from fusion_hero_os.core.tailscale_quantize_selfmod import ensure_assist_nodes

        return ensure_assist_nodes()

    return await asyncio.to_thread(_run)


@router.post("/api/mesh/ops/quantize-selfmod/modulate")
async def mesh_ops_quantize_selfmod_modulate(
    heroic: float = Query(0.0, ge=0.0, le=1.0),
) -> Dict[str, Any]:
    def _run():
        from fusion_hero_os.core.tailscale_quantize_selfmod import self_modulate

        return self_modulate(heroic_boost=heroic)

    return await asyncio.to_thread(_run)


@router.post("/api/mesh/ops/quantize-selfmod/cycle")
async def mesh_ops_quantize_selfmod_cycle(
    heroic: float = Query(0.0, ge=0.0, le=1.0),
) -> Dict[str, Any]:
    """Ensure assist nodes → self-mod params → quantized QUBO run (local fan-out)."""

    def _run():
        from fusion_hero_os.core.tailscale_quantize_selfmod import run_full_cycle

        return run_full_cycle(heroic_boost=heroic)

    return await asyncio.to_thread(_run)


@router.get("/api/mesh/ops/p1")
async def mesh_ops_p1() -> Dict[str, Any]:
    return await asyncio.to_thread(_registry_stubs_cleared)


@router.post("/api/mesh/ops/mainframe-laden")
async def mesh_ops_mainframe_laden(
    include_code_registry: bool = Query(True),
) -> Dict[str, Any]:
    def _run():
        from fusion_hero_os.modules.mainframe_laden import load_all

        return load_all(include_code_registry=include_code_registry)

    return await asyncio.to_thread(_run)


# ---------------------------------------------------------------------------
# Poly-Mesh DNS (encrypted mesh IP) + heroic once-URL
# ---------------------------------------------------------------------------


@router.post("/api/mesh/ops/once")
@router.get("/api/mesh/ops/once/mint")
async def mesh_ops_once_mint(
    port: int = Query(42069, description="Target local/mesh service port"),
    ttl_sec: int = Query(900, ge=60, le=86400),
    name: Optional[str] = Query(None, description="Optional mugen-tsuky.chan name"),
    path: str = Query("/", description="Path after redeem"),
) -> Dict[str, Any]:
    """Mint single-use mugen-tsuky.chan URL + polymesh encrypted DNS label."""

    def _run():
        from fusion_hero_os.core.mugen_tsuky_chan import mint_once
        from fusion_hero_os.ports import get_ports

        try:
            p = int(port) if port else get_ports().dashboard
        except Exception:
            p = 42069
        return mint_once(port=p, ttl_sec=ttl_sec, name=name)

    return await asyncio.to_thread(_run)


@router.get("/api/mesh/ops/dns/encrypt")
async def mesh_ops_dns_encrypt(
    ip: Optional[str] = Query(None, description="Mesh IP (default: self Tailscale)"),
    port: int = Query(42069),
    name: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Return encrypted mesh-IP token + heroic polymesh DNS label (not ICANN)."""

    def _run():
        from fusion_hero_os.core.poly_mesh_once_url import (
            encrypt_mesh_ip,
            heroic_dns_label,
            pick_heroic_name,
            mint_from_tailscale,
        )

        if ip:
            enc = encrypt_mesh_ip(ip, port)
            hero = name or pick_heroic_name()
            return {
                "ok": True,
                "mesh_ip": ip,
                "port": port,
                "encrypted_mesh_ip": enc,
                "heroic_name": hero,
                "polymesh_dns": heroic_dns_label(hero, enc),
                "note": "polymesh_dns = mesh-local encrypted label, not public DNS",
            }
        return mint_from_tailscale(port=port, name=name)

    return await asyncio.to_thread(_run)


@router.get("/api/mesh/ops/identity")
async def mesh_ops_identity(propagate: bool = Query(False)) -> Dict[str, Any]:
    """Comädchen × alte-frau95g × pr0-chan identity (voice/visual/TTS contract)."""

    def _run():
        from fusion_hero_os.core.comaedchen_identity import propagate as prop, status

        return prop() if propagate else status()

    return await asyncio.to_thread(_run)


@router.get("/api/mesh/ops/schwerkraft")
@router.post("/api/mesh/ops/schwerkraft/execute")
async def mesh_ops_schwerkraft(
    force: bool = Query(False),
    control_only: bool = Query(False),
) -> Dict[str, Any]:
    """Schwerkraftserver: dual multi-model lossless gate + git→poly-mesh ingest."""

    def _run():
        from fusion_hero_os.core.schwerkraftserver import dual_multi_model_control, execute

        if control_only:
            return dual_multi_model_control()
        return execute(force=force)

    return await asyncio.to_thread(_run)


@router.get("/api/mesh/ops/mtc")
@router.get("/api/mesh/ops/mtc/status")
async def mesh_ops_mtc_status() -> Dict[str, Any]:
    """mugen-tsuky.chan — central clear status (protocol propagation)."""

    def _run():
        from fusion_hero_os.core.mugen_tsuky_chan import propagate

        return propagate()

    return await asyncio.to_thread(_run)


@router.get("/api/mesh/ops/mtc/roll")
@router.post("/api/mesh/ops/mtc/roll")
@router.get("/api/mesh/ops/rollation")  # legacy alias
@router.post("/api/mesh/ops/rollation")
async def mesh_ops_mtc_roll(
    day: Optional[str] = Query(None, description="UTC day YYYY-MM-DD (default: yesterday)"),
    depth: int = Query(8, ge=1, le=64),
) -> Dict[str, Any]:
    """mugen-tsuky.chan day roll (clear fields; body obfuscated)."""

    def _run():
        from fusion_hero_os.core.mugen_tsuky_chan import roll

        return roll(day, depth=depth)

    return await asyncio.to_thread(_run)


@router.get("/once/{heroic_name}/{once_id}")
async def mesh_once_redeem(heroic_name: str, once_id: str):
    """Redeem single-use heroic URL → HTML handoff (one shot)."""
    from fastapi.responses import HTMLResponse, JSONResponse

    def _run():
        from fusion_hero_os.core.poly_mesh_once_url import redeem_once

        return redeem_once(once_id)

    result = await asyncio.to_thread(_run)
    if not result.get("ok"):
        return JSONResponse(result, status_code=410)

    # Prefer same-host relative dashboard path when target is local mesh service
    target = result.get("target_path") or "/"
    mesh_ip = result.get("mesh_ip")
    port = result.get("port") or 42069
    hero = result.get("heroic_name") or heroic_name
    # Client-side: open mesh URL if on tailnet; else show encrypted handle
    html = f"""<!DOCTYPE html>
<html lang="de"><head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>ONCE · {hero}</title>
<style>
body{{margin:0;min-height:100vh;display:grid;place-items:center;font-family:system-ui,sans-serif;
background:#0a0614;color:#f4f0ff}}
.card{{max-width:28rem;padding:2rem;border:1px solid rgba(240,193,75,.35);border-radius:12px;
background:rgba(12,8,24,.85)}}
h1{{font-size:1.1rem;letter-spacing:.08em;text-transform:uppercase;color:#f0c14b}}
code{{word-break:break-all;color:#5ce1e6}}
a.btn{{display:inline-block;margin-top:1rem;padding:.6rem 1rem;background:linear-gradient(135deg,#3a2a10,#1a3040);
border:1px solid #f0c14b;border-radius:8px;color:#fff;text-decoration:none}}
.muted{{opacity:.7;font-size:.85rem}}
</style></head><body>
<div class="card">
<h1>⚡ {hero}</h1>
<p>Einmal-URL eingelöst. Token verbraucht.</p>
<p class="muted">Mesh-Ziel (Tailscale):</p>
<p><code>{mesh_ip}:{port}{target}</code></p>
<p class="muted">Verschlüsselte Mesh-IP:</p>
<p><code>{result.get("enc_ip","")}</code></p>
<a class="btn" href="{target}">Weiter zum Dienst (lokal / Funnel)</a>
<p class="muted">Wenn du im Poly-Mesh bist: <code>http://{mesh_ip}:{port}{target}</code></p>
<script>
// Auto-nav to local path when served from same funnel host
setTimeout(function(){{ try {{ location.replace({json.dumps(target)}); }} catch(e){{}} }}, 1200);
</script>
</div></body></html>"""
    return HTMLResponse(html)
