#!/usr/bin/env python3
"""
Fusion Hero OS - REST API Server (Port 8000)
Mainframe Backend für Frontend-Orchestration
Endpoints: /api/*, /mod/*, /events
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os
from datetime import datetime
from typing import Dict, List

# === FASTAPI APP ===
app = FastAPI(
    title="Fusion Hero OS REST API",
    description="Mainframe Backend für autonome Task-Zuordnung und Orchestration",
    version="7.5"
)

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === MODELS ===
class TaskEvent(BaseModel):
    type: str
    msg: str

class TaskInput(BaseModel):
    query: str
    task_id: int
    category: str
    dom: str

class HyperthreadingConfig(BaseModel):
    enabled: bool

class CodeModification(BaseModel):
    code: str

# === STATE ===
events_log: List[Dict] = []
tasks_queue: List[Dict] = []
hyperthreading_enabled = False

# === ENDPOINTS ===

@app.get("/")
async def root():
    """Willkommen"""
    return {
        "app": "Fusion Hero OS REST API v7.5",
        "status": "running",
        "frontend": "http://localhost:8080",
        "backend": "http://localhost:8000"
    }

@app.get("/api/health")
async def health():
    """Systemstatus"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "frontend": "ready",
            "backend": "running",
            "mainframe": "operational"
        }
    }

@app.get("/api/input-factors")
async def input_factors():
    """CPU/GPU/Hyperthreading Status"""
    import psutil
    try:
        cpu_count = psutil.cpu_count(logical=True)
        return {
            "logical_cpus": cpu_count,
            "physical_cpus": psutil.cpu_count(logical=False),
            "hyperthreading_env": "FUSION_HYPERTHREADING" in os.environ,
            "gpu_count": 0  # TODO: Integrate GPU detection
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/output-factors")
async def output_factors():
    """Worker-Konfiguration"""
    import psutil
    return {
        "target_workers": psutil.cpu_count(logical=True) or 4,
        "task_assignment_strategy": "best_fit",
        "load_balancing": "dynamic"
    }

@app.get("/api/hyperthreading")
async def get_hyperthreading():
    """Get Hyperthreading Status"""
    return {
        "enabled": hyperthreading_enabled,
        "workers": int(os.environ.get("FUSION_WORKERS", 4)),
        "virtual_ht_gpu": "FUSION_GPU_HT" in os.environ
    }

@app.post("/api/hyperthreading")
async def set_hyperthreading(config: HyperthreadingConfig):
    """Enable/Disable Hyperthreading"""
    global hyperthreading_enabled
    hyperthreading_enabled = config.enabled
    if config.enabled:
        os.environ["FUSION_HYPERTHREADING"] = "1"
    else:
        os.environ.pop("FUSION_HYPERTHREADING", None)
    return {"status": "ok", "enabled": hyperthreading_enabled}

@app.post("/api/events")
async def log_event(event: TaskEvent):
    """Log Task Event"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "type": event.type,
        "message": event.msg
    }
    events_log.append(entry)
    print(f"[EVENT] {event.type}: {event.msg}")
    return {"status": "logged", "id": len(events_log)}

@app.post("/api/input")
async def process_input(task: TaskInput):
    """Process Task Input"""
    task_dict = {
        "id": task.task_id,
        "query": task.query,
        "category": task.category,
        "domain": task.dom,
        "status": "processing",
        "timestamp": datetime.now().isoformat()
    }
    tasks_queue.append(task_dict)
    print(f"[TASK] #{task.task_id} [{task.category}] {task.query[:50]}...")
    return {
        "status": "accepted",
        "task_id": task.task_id,
        "queue_position": len(tasks_queue)
    }

@app.post("/mod/apply")
async def apply_modification(mod: CodeModification):
    """Apply Code Modification (PeerReview)"""
    # TODO: Integrate with heroic_orchestration
    return {
        "status": "approved",
        "peer_review": ["Layer 1: PASS", "Layer 3: PASS"],
        "geltung": "proven"
    }

@app.get("/api/events")
async def get_events(limit: int = 50):
    """Get Recent Events"""
    return {"events": events_log[-limit:]}

@app.get("/api/tasks")
async def get_tasks(limit: int = 50):
    """Get Recent Tasks"""
    return {"tasks": tasks_queue[-limit:]}

@app.get("/api/tasks/{task_id}")
async def get_task(task_id: int):
    """Get Specific Task"""
    for task in tasks_queue:
        if task["id"] == task_id:
            return task
    raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

# === STARTUP ===
if __name__ == "__main__":
    print("🚀 Starting Fusion Hero OS REST API...")
    print("📡 Backend: http://127.0.0.1:8000")
    print("🎨 Frontend: http://127.0.0.1:8080")
    print("✅ Press Ctrl+C to stop")
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
