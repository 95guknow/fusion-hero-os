# Fusion Hero OS — Agent Memory (synced 2026-07-05)

## Repo
- Kanonisch: `C:\Users\Admin\fusion-hero-os` → github.com/95guknow/fusion-hero-os
- HEAD: `9fa41bf` (main = origin/main)
- Version: v8

## Agent-Kontext (docs/agent_context/claude_memory)
- MEMORY.md — Index
- pending-code-honesty-audit.md — teils offen (app.py sweep, v5.22 stubs)
- repo-background-automation.md — auto_save.ps1 kann Git-Baum bewegen
- heroic-qubo-algorithm-audit.md — SA-Bug gefixt, LoRA-Überclaim korrigiert

## Grok Intern
- Global skills: fusion-hero-os, heroic-core-foundation, alte-frau-95g, mainframe-laden
- Sync: `sync_grok_intern.ps1` bei Session-Start
- GROK_EXPORT_REQUEST: 3 Module als Scaffold nachgeholt (2026-07-05)

## CI
- Root `Cargo.toml` Workspace (pms_rust_kernel + rust_engine)
- `cargo build --workspace` in ci.yml (main/develop)

## Code-Honesty
- Dashboard WebSocket-Events = Demo, keine echte Peer-Review
- Image/Connectors = Dry-Run default