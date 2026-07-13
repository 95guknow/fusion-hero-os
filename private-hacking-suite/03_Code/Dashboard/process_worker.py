# -*- coding: utf-8 -*-
"""Worker-Prozesse — schwere Ausgabe/Code/Module hier, nicht im Eingabe-Layer."""
from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

DASHBOARD = Path(__file__).resolve().parent
CODE_ROOT = DASHBOARD.parent
WORKER_SCRIPT = DASHBOARD / "worker_runner.py"

_executor_proc: Optional[ProcessPoolExecutor] = None
_executor_io: Optional[ThreadPoolExecutor] = None
_jobs: Dict[str, dict] = {}
_MAX_JOBS = 200


@dataclass
class JobRecord:
    job_id: str
    status: str = "queued"
    kind: str = ""
    ack: str = ""
    result: Optional[dict] = None
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    finished_at: Optional[float] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        if d["result"] and isinstance(d["result"], dict):
            resp = d["result"].get("response", "")
            if isinstance(resp, str) and len(resp) > 2000:
                d["result"] = {**d["result"], "response": resp[:2000] + "\n…(Worker-Output gekuerzt)"}
        return d


def _get_proc_pool() -> ProcessPoolExecutor:
    global _executor_proc
    if _executor_proc is None:
        workers = max(1, min(4, (os.cpu_count() or 2) // 2))
        _executor_proc = ProcessPoolExecutor(max_workers=workers)
    return _executor_proc


def _get_io_pool() -> ThreadPoolExecutor:
    global _executor_io
    if _executor_io is None:
        _executor_io = ThreadPoolExecutor(max_workers=4, thread_name_prefix="fusion-io")
    return _executor_io


def warm_pools() -> dict:
    """Autoloader: Pools vorwärmen ohne Job."""
    proc = _get_proc_pool()
    io = _get_io_pool()
    return {
        "process_pool": {"warm": True, "workers": proc._max_workers},
        "io_pool": {"warm": True, "workers": io._max_workers},
    }


def pool_status() -> dict:
    return {
        "process_pool": {
            "warm": _executor_proc is not None,
            "workers": _executor_proc._max_workers if _executor_proc else 0,
        },
        "io_pool": {
            "warm": _executor_io is not None,
            "workers": _executor_io._max_workers if _executor_io else 0,
        },
    }


def _trim_jobs() -> None:
    if len(_jobs) <= _MAX_JOBS:
        return
    oldest = sorted(_jobs.items(), key=lambda x: x[1].get("created_at", 0))[: len(_jobs) - _MAX_JOBS]
    for jid, _ in oldest:
        _jobs.pop(jid, None)


def register_job(job_id: str, kind: str, ack: str = "") -> JobRecord:
    rec = JobRecord(job_id=job_id, kind=kind, ack=ack, status="queued")
    _jobs[job_id] = rec.to_dict()
    _trim_jobs()
    return rec


def get_job(job_id: str) -> Optional[dict]:
    return _jobs.get(job_id)


def list_jobs(limit: int = 20) -> List[dict]:
    items = sorted(_jobs.values(), key=lambda j: j.get("created_at", 0), reverse=True)
    return items[:limit]


def _run_in_subprocess(job_payload: dict) -> dict:
    """Isolierter Worker-Prozess fuer CPU-lastige Jobs."""
    if not WORKER_SCRIPT.exists():
        return _run_in_thread(job_payload)
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join([
        str(DASHBOARD), str(CODE_ROOT), env.get("PYTHONPATH", ""),
    ])
    proc = subprocess.run(
        [sys.executable, str(WORKER_SCRIPT)],
        input=json.dumps(job_payload, default=str),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        cwd=str(DASHBOARD),
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or proc.stdout or "worker failed")[-500:])
    return json.loads(proc.stdout)


def _run_in_thread(job_payload: dict) -> dict:
    """IO-Worker-Thread — keine schwere Logik im Eingabe-Layer."""
    from worker_tasks import execute_job
    result = execute_job(job_payload)
    _apply_worker_side_effects(job_payload, result)
    return result


def _apply_worker_side_effects(job_payload: dict, result: dict) -> None:
    """Sync Registry-State zurueck in app-Globals (nur nach Worker)."""
    try:
        import app as fusion_app
        from module_registry import get_registry
        for ex in result.get("executed") or []:
            if ex.get("intent") in ("load_all", "mainframe_load") and ex.get("status") == "ok":
                reg = get_registry()
                if reg._last_load_result:
                    fusion_app._sync_globals_from_registry(reg._last_load_result)
                    fusion_app._invalidate_health_cache()
    except Exception:
        pass


def _is_heavy(job_payload: dict) -> bool:
    """Nur CPU-bound in separaten Prozess — Registry-Jobs im Thread (State-Sync)."""
    intents = set(job_payload.get("intents") or [])
    kind = job_payload.get("kind", "")
    proc_intents = {"benchmark", "qubo"}
    proc_kinds = {"benchmark", "qubo"}
    return bool(intents & proc_intents) or kind in proc_kinds


def submit_job(job_payload: dict, ack: str = "") -> str:
    job_id = job_payload["job_id"]
    register_job(job_id, job_payload.get("kind", "?"), ack)

    def _done(fut):
        rec = _jobs.get(job_id, {})
        try:
            result = fut.result()
            _apply_worker_side_effects(job_payload, result)
            rec.update({
                "status": "done",
                "result": result,
                "finished_at": time.time(),
            })
        except Exception as exc:
            rec.update({
                "status": "error",
                "error": str(exc),
                "finished_at": time.time(),
            })
        _jobs[job_id] = rec

    _jobs[job_id]["status"] = "running"

    if _is_heavy(job_payload):
        fut = _get_proc_pool().submit(_run_in_subprocess, job_payload)
    else:
        fut = _get_io_pool().submit(_run_in_thread, job_payload)
    fut.add_done_callback(_done)
    return job_id


async def submit_job_async(job_payload: dict, ack: str = "") -> str:
    loop = asyncio.get_event_loop()
    job_id = job_payload["job_id"]
    register_job(job_id, job_payload.get("kind", "?"), ack)
    _jobs[job_id]["status"] = "running"
    try:
        if _is_heavy(job_payload):
            result = await loop.run_in_executor(_get_proc_pool(), _run_in_subprocess, job_payload)
        else:
            result = await loop.run_in_executor(_get_io_pool(), _run_in_thread, job_payload)
        _jobs[job_id].update({"status": "done", "result": result, "finished_at": time.time()})
    except Exception as exc:
        _jobs[job_id].update({"status": "error", "error": str(exc), "finished_at": time.time()})
    return job_id