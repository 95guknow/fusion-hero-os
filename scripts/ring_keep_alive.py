#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ring-Leben keep-alive — no pause.

Pings /api/ring/heartbeat (and light health). Restarts uvicorn if the ring is dead.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "03_Code" / "Dashboard"
PYTHON = os.environ.get(
    "FUSION_PYTHON",
    r"C:\Users\Admin\venv\Scripts\python.exe"
    if Path(r"C:\Users\Admin\venv\Scripts\python.exe").is_file()
    else sys.executable,
)
BASE_URL = os.environ.get("FUSION_RING_URL", "http://127.0.0.1:8000")
INTERVAL = float(os.environ.get("FUSION_RING_INTERVAL_SEC", "20"))
FAILS_BEFORE_RESTART = int(os.environ.get("FUSION_RING_FAILS", "3"))
LOCK_DIR = Path.home() / ".fusion-hero-os" / "process_locks"


def _ping(path: str, timeout: float = 5.0) -> dict:
    url = f"{BASE_URL.rstrip('/')}{path}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw) if raw else {}


def _clear_locks() -> None:
    if not LOCK_DIR.is_dir():
        return
    for p in LOCK_DIR.glob("dashboard_*.lock"):
        try:
            p.unlink()
        except OSError:
            pass


def _kill_uvicorn() -> None:
    try:
        import psutil  # type: ignore

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmd = " ".join(proc.info.get("cmdline") or [])
                if "uvicorn" in cmd and "app:app" in cmd:
                    proc.kill()
            except (psutil.Error, TypeError):
                continue
    except Exception:
        # Windows fallback
        if os.name == "nt":
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    (
                        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" "
                        "| Where-Object { $_.CommandLine -match 'uvicorn app:app' } "
                        "| ForEach-Object { Stop-Process -Id $_.ProcessId -Force -EA SilentlyContinue }"
                    ),
                ],
                capture_output=True,
                timeout=30,
            )


def _start_dashboard() -> None:
    env = os.environ.copy()
    env.setdefault("FUSION_BOOT_PHASE", "light")
    env.setdefault("FUSION_AUTO_LOAD", "0")
    env.setdefault("FUSION_PRELOAD_ALL", "0")
    env.setdefault("FUSION_ALL_MODULES", "0")
    env.setdefault("FUSION_RING_LIFE_FAST", "1")
    env.setdefault("FUSION_SUPABASE_SYNC", "0")
    env.setdefault("FUSION_MAINFRAME_DAEMONS", "1")
    env.setdefault("FUSION_HYPERTHREADING", "1")
    env.setdefault("PORT", "8000")
    env.setdefault("FUSION_BACKEND_PORT", "8000")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    _clear_locks()
    creation = 0
    if os.name == "nt":
        creation = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) | getattr(
            subprocess, "DETACHED_PROCESS", 0x00000008
        )
    subprocess.Popen(
        [
            PYTHON,
            "-m",
            "uvicorn",
            "app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
            "--log-level",
            "warning",
            "--timeout-keep-alive",
            "5",
        ],
        cwd=str(DASH),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation,
        start_new_session=(os.name != "nt"),
    )


def main() -> int:
    fails = 0
    print(
        f"[ring-life] no-pause keep-alive url={BASE_URL} interval={INTERVAL}s "
        f"fails_before_restart={FAILS_BEFORE_RESTART}",
        flush=True,
    )
    # ensure born
    try:
        _ping("/api/ring/heartbeat", timeout=8)
        print("[ring-life] first beat OK", flush=True)
    except Exception as exc:
        print(f"[ring-life] cold start: {exc}", flush=True)
        _kill_uvicorn()
        time.sleep(1)
        _start_dashboard()
        time.sleep(8)

    while True:
        try:
            beat = _ping("/api/ring/heartbeat", timeout=6)
            light = _ping("/api/health?light=true", timeout=6)
            fails = 0
            ring = beat.get("ring") or {}
            print(
                f"[ring-life] ALIVE beats={ring.get('beats')} "
                f"uptime={ring.get('uptime_sec')}s "
                f"health={light.get('status')} phase={ring.get('phase')}",
                flush=True,
            )
        except Exception as exc:
            fails += 1
            print(f"[ring-life] MISS {fails}/{FAILS_BEFORE_RESTART}: {exc}", flush=True)
            if fails >= FAILS_BEFORE_RESTART:
                print("[ring-life] RESTART dashboard (ring dead)", flush=True)
                _kill_uvicorn()
                time.sleep(2)
                _start_dashboard()
                fails = 0
                time.sleep(10)
                continue
        time.sleep(INTERVAL)


if __name__ == "__main__":
    raise SystemExit(main())
