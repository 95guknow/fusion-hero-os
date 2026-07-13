# Fusion Hero OS - Deployment Guide

## Quick Start

### Prerequisites
```bash
pip install fastapi uvicorn psutil
```

### Single Process: Dashboard GUI + API (Port 8000)
```bash
cd 03_Code/Dashboard
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Or on Windows:
```bat
run_backend.bat
```

### Auto-Load (recommended)
```powershell
powershell -File start_all.ps1
```

### Access
- **Standard GUI**: http://127.0.0.1:8000
- **API Health**: http://127.0.0.1:8000/api/health
- **API Docs**: http://127.0.0.1:8000/docs
- **WebSocket**: ws://127.0.0.1:8000/ws

### Optional: NiceGUI Legacy (Port 8080)
Only if needed — not the default GUI:
```powershell
powershell -File start_all.ps1 -NiceGUI
```
Or manually: `run_workspace.bat` → http://127.0.0.1:8080

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│     Standard GUI (FastAPI + HTML, Port 8000)            │
│  - templates/index.html (Dashboard)                     │
│  - WebSocket /ws (Live Events)                          │
│  - REST API /api/*                                      │
└────────────────────┬────────────────────────────────────┘
                     │ Python imports
                     ▼
┌─────────────────────────────────────────────────────────┐
│           Mainframe Core (in-process)                   │
│  - Heroic Orchestration                                 │
│  - Hyperthreading Control                               │
│  - Agent Supervisor                                     │
│  - QUBO / AutoLoad                                      │
└─────────────────────────────────────────────────────────┘
```

---

## Deployment Status

| Component | Status | Location | Port |
|-----------|--------|----------|------|
| Standard GUI | Ready | `03_Code/Dashboard/app.py` | 8000 |
| NiceGUI Legacy | Optional | `03_Code/Dashboard/workspace.py` | 8080 |
| Reference REST | Dev/Ref | `03_Code/reference/rest_api_server.py` | — |

---

## API Example Usage

### Health Check
```bash
curl http://127.0.0.1:8000/api/health
```

### GUI Status
```bash
curl http://127.0.0.1:8000/api/gui/status
```

### Enable Hyperthreading
```bash
curl -X POST http://127.0.0.1:8000/api/hyperthreading \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
```

---

## Troubleshooting

### Port 8000 already in use
```bat
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### NiceGUI conflicts with other apps on 8080
Do not start NiceGUI unless needed. Default is port 8000 only.