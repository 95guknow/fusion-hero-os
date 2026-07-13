# -*- coding: utf-8 -*-
"""GUI → Eingabe-Layer — nur Ack; Worker liefert Ausgabe."""
from __future__ import annotations

import asyncio
from typing import Any, Optional

import requests
from nicegui import run, ui

from gui.config import API_BASE, SIGNAL_CLIENT_ID, SIGNAL_LAYER_DEFAULT


def api_call(method: str, path: str, timeout: int = 30, **kwargs) -> dict:
    url = f"{API_BASE}{path}"
    resp = getattr(requests, method)(url, timeout=timeout, **kwargs)
    resp.raise_for_status()
    return resp.json()


async def call_api(method: str, path: str, timeout: int = 30, **kwargs) -> dict:
    return await run.io_bound(lambda: api_call(method, path, timeout=timeout, **kwargs))


async def submit_input(
    kind: str,
    message: str = "",
    code: str = "",
    payload: Optional[dict] = None,
    history: Optional[list] = None,
    wait_timeout: int = 180,
    notify: bool = True,
) -> dict:
    ack = await call_api(
        "post",
        "/api/input",
        json={
            "kind": kind,
            "message": message,
            "code": code,
            "payload": payload or {},
            "history": history or [],
        },
        timeout=10,
    )
    if not ack.get("accepted", True) and ack.get("error"):
        raise RuntimeError(ack["error"])
    if ack.get("sync") or ack.get("response"):
        return ack
    job_id = ack.get("job_id")
    if not job_id:
        return ack
    if notify:
        ui.notify(f"Worker {job_id}…", type="info")
    for _ in range(wait_timeout * 2):
        job = await call_api("get", f"/api/jobs/{job_id}", timeout=8)
        st = job.get("status")
        if st == "done":
            return job.get("result") or job
        if st == "error":
            raise RuntimeError(job.get("error", "Worker-Fehler"))
        await asyncio.sleep(0.5)
    raise TimeoutError(f"Worker {job_id} Timeout")


async def fetch_signal_pulse() -> dict:
    return await call_api(
        "get",
        f"/api/signal/health?layer={SIGNAL_LAYER_DEFAULT}&client={SIGNAL_CLIENT_ID}",
        timeout=12,
    )


async def fetch_health_full() -> dict:
    return await call_api("get", "/api/health?full=true", timeout=15)


async def fetch_jobs(limit: int = 12) -> list:
    data = await call_api("get", f"/api/jobs?limit={limit}", timeout=8)
    return data.get("jobs", [])