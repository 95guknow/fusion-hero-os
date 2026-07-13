# C ↔ Python IPC Bridge (v1.1)

Bridge between C Kernel and Python Userland. Routes to `fusion_hero_os` Dispatcher
(including deepened Timespace, LLM-EA, ImageOrchestrator modules).

## Transports

| Transport | Server | Platform |
|-----------|--------|----------|
| TCP | `fhos_ipc_server.py` | Windows, Linux, macOS |
| AF_UNIX | `fhos_ipc_server.c` | Linux, WSL |
| in-process | `fhos_ipc_client.auto_client()` fallback | always (no socket) |

Default TCP: `127.0.0.1:19753`

## Files

- `protocol.py` — shared header + message types
- `fhos_ipc_server.c` — C AF_UNIX MVP (echo + status)
- `fhos_ipc_server.py` — Python TCP server (full dispatch)
- `fhos_ipc_client.py` — client (TCP / unix / in-process)
- `fusion_hero_os/bridge/` — router + gateway

## Message Types

- `0x01` PING
- `0x10` DISPATCH — JSON `{"module": "...", "payload": {...}}`
- `0x20` MATH_STATUS
- `0x21` ORCHESTRATOR_STATUS
- `0x22` LIST_MODULES

## Usage

```powershell
python start_fusion_hero.py --with-dashboard
# API: GET http://127.0.0.1:8000/api/bridge/ipc/status
# API: POST http://127.0.0.1:8000/api/bridge/ipc/dispatch
```