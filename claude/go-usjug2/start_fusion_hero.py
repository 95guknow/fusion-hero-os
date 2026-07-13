#!/usr/bin/env python3
"""
Fusion Hero OS - Unified Launcher v8
====================================

Starts the C↔Python IPC Bridge (TCP on Windows, AF_UNIX on Linux/WSL)
and optionally the Dashboard.

Usage:
    python start_fusion_hero.py
    python start_fusion_hero.py --bridge-only
    python start_fusion_hero.py --with-dashboard
    python start_fusion_hero.py --list-versions
"""

from __future__ import annotations

import argparse
import logging
import os
import platform
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path(__file__).parent.resolve()
BRIDGE_DIR = PROJECT_ROOT / "kernel" / "bridge"
C_SERVER_SRC = BRIDGE_DIR / "fhos_ipc_server.c"
C_SERVER_BIN = BRIDGE_DIR / "fhos_ipc_server"
PY_SERVER = BRIDGE_DIR / "fhos_ipc_server.py"
DASHBOARD_DIR = PROJECT_ROOT / "03_Code" / "Dashboard"
DASHBOARD_SCRIPT = DASHBOARD_DIR / "app.py"
ARCHIVE_DIR = PROJECT_ROOT / "06_Master_Archive"
SOCKET_PATH = "/tmp/fusion_hero_ipc.sock"
TCP_PORT = 19753
DASHBOARD_HOST = os.getenv("FUSION_BACKEND_HOST", "0.0.0.0")
DASHBOARD_PORT = int(os.getenv("FUSION_BACKEND_PORT", "8000"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("FusionHeroOS")


class ProcessManager:
    def __init__(self) -> None:
        self.processes: List[subprocess.Popen] = []

    def add(self, process: Optional[subprocess.Popen]) -> None:
        if process:
            self.processes.append(process)

    def shutdown_all(self) -> None:
        logger.info("Shutting down all components...")
        for proc in reversed(self.processes):
            if proc and proc.poll() is None:
                try:
                    proc.terminate()
                    proc.wait(timeout=4)
                except subprocess.TimeoutExpired:
                    proc.kill()
        self.processes.clear()
        logger.info("All components stopped cleanly.")


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def compile_c_server() -> bool:
    if not C_SERVER_SRC.exists():
        return False
    if C_SERVER_BIN.exists() and C_SERVER_BIN.stat().st_mtime >= C_SERVER_SRC.stat().st_mtime:
        return True
    if is_windows():
        logger.info("Skipping C compile on Windows (use Python TCP bridge).")
        return False
    logger.info("Compiling C IPC Bridge server...")
    cmd = ["gcc", "-Wall", "-Wextra", "-O2", "-o", str(C_SERVER_BIN), str(C_SERVER_SRC)]
    try:
        subprocess.run(cmd, cwd=BRIDGE_DIR, check=True, capture_output=True, text=True)
        logger.info("C server compiled successfully.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        logger.warning("C server compile failed: %s", e)
        return False


def start_python_tcp_bridge(manager: ProcessManager) -> Optional[subprocess.Popen]:
    if not PY_SERVER.exists():
        return None
    logger.info("Starting Python TCP IPC Bridge (port %d)...", TCP_PORT)
    proc = subprocess.Popen(
        [sys.executable, str(PY_SERVER), "--port", str(TCP_PORT)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    manager.add(proc)
    time.sleep(0.8)
    logger.info("Python IPC Bridge active (PID: %s)", proc.pid)
    return proc


def start_c_unix_bridge(manager: ProcessManager) -> Optional[subprocess.Popen]:
    if not C_SERVER_BIN.exists() or is_windows():
        return None
    if os.path.exists(SOCKET_PATH):
        try:
            os.unlink(SOCKET_PATH)
        except OSError:
            pass
    logger.info("Starting C AF_UNIX IPC Bridge...")
    proc = subprocess.Popen(
        [str(C_SERVER_BIN)],
        cwd=BRIDGE_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    manager.add(proc)
    time.sleep(0.7)
    logger.info("C IPC Bridge active (PID: %s)", proc.pid)
    return proc


def start_bridge(manager: ProcessManager) -> Optional[subprocess.Popen]:
    """Windows: Python TCP. Linux: try C unix, fallback Python TCP."""
    if is_windows():
        return start_python_tcp_bridge(manager)
    if compile_c_server():
        bridge = start_c_unix_bridge(manager)
        if bridge and bridge.poll() is None:
            return bridge
    return start_python_tcp_bridge(manager)


def start_dashboard(manager: ProcessManager) -> Optional[subprocess.Popen]:
    script = DASHBOARD_SCRIPT if DASHBOARD_SCRIPT.exists() else DASHBOARD_DIR / "heroic_core_gui.py"
    if not script.exists():
        logger.warning("Dashboard script not found. Skipping.")
        return None
    logger.info("Starting Dashboard (%s)...", script.name)
    env = os.environ.copy()
    env["FUSION_AUTO_LOAD"] = "0"
    env["FUSION_ALL_MODULES"] = "0"
    py_path = str(PROJECT_ROOT)
    code_path = str(PROJECT_ROOT / "03_Code")
    env["PYTHONPATH"] = f"{py_path}{os.pathsep}{code_path}"
    try:
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app:app",
                "--host",
                DASHBOARD_HOST,
                "--port",
                str(DASHBOARD_PORT),
            ],
            cwd=DASHBOARD_DIR,
            env=env,
        )
        manager.add(proc)
        logger.info(
            "Dashboard started (PID: %s) → http://127.0.0.1:%d (LAN: host=%s)",
            proc.pid,
            DASHBOARD_PORT,
            DASHBOARD_HOST,
        )
        return proc
    except Exception as e:
        logger.error("Failed to start Dashboard: %s", e)
        return None


def list_archived_versions() -> None:
    print("\nAvailable Archived Beta Versions / Historical States:\n")
    if not ARCHIVE_DIR.exists():
        print("No archive directory found.")
        return
    items = sorted([p for p in ARCHIVE_DIR.iterdir() if p.is_dir() or p.suffix in (".md", ".pdf")])
    for item in items[:30]:
        print(f"  - {item.name}")
    if len(items) > 30:
        print(f"  ... and {len(items) - 30} more items")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fusion Hero OS Unified Launcher v8")
    parser.add_argument("--bridge-only", action="store_true")
    parser.add_argument("--with-dashboard", action="store_true")
    parser.add_argument("--list-versions", action="store_true")
    args = parser.parse_args()

    if args.list_versions:
        list_archived_versions()
        return

    print("\n" + "=" * 64)
    print("   FUSION HERO OS - LAUNCHER v8")
    print("   C↔Python IPC Bridge + Deepened Modules")
    print("=" * 64 + "\n")

    manager = ProcessManager()

    def shutdown_handler(sig, frame):
        manager.shutdown_all()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    bridge = start_bridge(manager)
    if not bridge or bridge.poll() is not None:
        logger.critical("Bridge server failed to start.")
        manager.shutdown_all()
        sys.exit(1)

    if args.with_dashboard:
        start_dashboard(manager)

    try:
        transport = "tcp" if is_windows() else "unix_or_tcp"
        logger.info("Bridge transport: %s | API: GET /api/bridge/ipc/status", transport)
        if args.bridge_only and bridge.stdout:
            for line in bridge.stdout:
                print(line, end="")
        else:
            logger.info("Press Ctrl+C to shut down.\n")
            while True:
                time.sleep(1)
                if bridge.poll() is not None:
                    logger.error("Bridge server exited unexpectedly.")
                    break
    except KeyboardInterrupt:
        pass
    finally:
        manager.shutdown_all()
        print("\nFusion Hero OS stopped cleanly.\n")


if __name__ == "__main__":
    main()