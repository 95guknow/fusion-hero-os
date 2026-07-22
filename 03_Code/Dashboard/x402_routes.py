# -*- coding: utf-8 -*-
"""API: x402 full security stack status + run."""
from __future__ import annotations

import hmac
import os
import sys
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

_ROOT = Path(__file__).resolve().parents[2]
for p in (str(_ROOT), str(_ROOT / "03_Code")):
    if p not in sys.path:
        sys.path.insert(0, p)

router = APIRouter(tags=["x402-security"])

# Each run spawns a subprocess with a 180s timeout; without a cap an attacker
# (or a busy operator) can queue unbounded concurrent long-lived subprocesses.
_MAX_CONCURRENT_RUNS = int(os.getenv("FUSION_X402_MAX_CONCURRENT", "1"))
_run_lock = threading.Lock()
_runs_in_flight = 0

# broadcast_onchain triggers a real on-chain transaction, not just a dry run —
# gate it behind the same admin token as the dashboard's other heavy/sensitive
# endpoints once configured (unset by default; see app.py).
_ADMIN_TOKEN = os.getenv("FUSION_DASHBOARD_ADMIN_TOKEN")


class X402RunIn(BaseModel):
    budget_eur: float = Field(default=500.0, ge=0)
    broadcast_onchain: bool = False


@router.get("/api/x402/status")
async def x402_status():
    from fusion_hero_os.core.x402_hackability_audit import status as threat_status
    from fusion_hero_os.core.x402_sandbox_audit import status as sandbox_status

    master = Path.home() / ".fusion" / "x402" / "x402_stack_master.json"
    master_data = None
    if master.is_file():
        import json

        try:
            master_data = json.loads(master.read_text(encoding="utf-8"))
        except Exception:
            master_data = None
    return {
        "ok": True,
        "threat": threat_status(),
        "sandbox": sandbox_status(),
        "master": master_data,
        "github": "https://github.com/95guknow/fusion-hero-os",
        "instagram": "https://www.instagram.com/95guknow/",
        "docs": "docs/security/X402_STACK.md",
    }


@router.post("/api/x402/run")
async def x402_run(body: X402RunIn, request: Request):
    import asyncio
    import subprocess

    global _runs_in_flight

    if body.broadcast_onchain and _ADMIN_TOKEN:
        supplied = request.headers.get("x-fusion-admin-token", "")
        if not hmac.compare_digest(supplied, _ADMIN_TOKEN):
            raise HTTPException(status_code=401, detail="admin token required for on-chain broadcast")

    with _run_lock:
        if _runs_in_flight >= _MAX_CONCURRENT_RUNS:
            raise HTTPException(
                status_code=429,
                detail="an x402 run is already in progress, retry shortly",
            )
        _runs_in_flight += 1

    def _run():
        cmd = [sys.executable, str(_ROOT / "scripts" / "run_x402_stack.py"), "--json-only"]
        if body.broadcast_onchain:
            cmd.append("--broadcast-onchain")
        r = subprocess.run(cmd, cwd=str(_ROOT), capture_output=True, text=True, timeout=180)
        import json

        try:
            return json.loads(r.stdout)
        except Exception:
            return {
                "ok": r.returncode == 0,
                "stdout": (r.stdout or "")[:4000],
                "stderr": (r.stderr or "")[:1000],
                "returncode": r.returncode,
            }

    try:
        return await asyncio.to_thread(_run)
    finally:
        with _run_lock:
            _runs_in_flight = max(0, _runs_in_flight - 1)
