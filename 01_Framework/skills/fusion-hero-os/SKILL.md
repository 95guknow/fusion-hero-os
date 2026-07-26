---
name: fusion-hero-os
description: Auto-load and operate Fusion Hero OS v13.0.0 operational (v8.3 stack + Stage-A/B) + v9.10 aspirational AscensionOS with Grok-intern ALTE_Frau_95g Heroic Core alignment. Use when the user mentions Fusion Hero OS, mainframe laden, auto load, heroic core, v8, v9, v10, Ascension, Grok intern abgleich, or propagation of v10.
---

# Fusion Hero OS v13.0.0 operational + v9.10 aspirational — Grok Intern Skill

## Version Stand
- **Fusion Hero OS Operative Kanon (Best Version):** **v13.0.0** (platform; inherits v8.3 functional stack + Stage-A/B privacy/consent/version gates)
- **Aspirational / Roadmap Track:** v9.10 (AscensionOS / CEC + AscensionCore + PersistentSisyphosCycle + GenerationalEvolutionEngine + v9.6/v9.7 modules)
- **Heroic Core (intern):** v10 platform + v8.3 modules + v9.10 aspirational bridge (`fusion_hero_os` + `heroic_math_engine` + `ascension_os`)
- **Repo:** `C:\Users\Admin\fusion-hero-os` → [95guknow/fusion-hero-os](https://github.com/95guknow/fusion-hero-os)
- **GitHub release target:** `v13.0.0` (operativer Kanon; Ascension v9.x bleibt loadable Roadmap)
- **Dashboard:** `03_Code/Dashboard/app.py` → `http://127.0.0.1:8000`
- **Ascension Layer:** registered in fusion_unified.yaml (loadable via QuadCoreBridge mode="ascension")

## Core Skills (global gespiegelt)
- `heroic-core-foundation` — unified ALTE_Frau_95g Heroic Core (v10 platform alignment)
- `alte-frau-95g` — Fusion Hero OS + Hyperthreading + Ascension bridge
- `mainframe-laden` — Mainframe-Modus + Vermerk-Pflicht (v13.0.0 alignment)

## Auto-Load (lokal)
```powershell
powershell -File C:\Users\Admin\fusion-hero-os\start_all.ps1
```

Startet:
1. **Standard-GUI** `http://127.0.0.1:8000` — FastAPI Dashboard
2. REST API + Mainframe + AutoLoad auf demselben Port
3. Hyperthreading (`FUSION_HYPERTHREADING=1`)
4. `sync_grok_intern.ps1` (GITHUB_SYNC.json + Kilo-Workspace)
5. NiceGUI `:8080` nur optional: `start_all.ps1 -NiceGUI`

## Hyperthreading (echt, gemessen)
- `parallel_anneal(backend="auto")` — Rust/rayon oder Numba-nogil
- Env: `FUSION_HYPERTHREADING=1`
- Konfig: `03_Code/Dashboard/hyperthreading_config.py`

| Endpoint | Funktion |
|---|---|
| `GET /api/hyperthreading` | Status (enabled, workers, logical_cpus) |
| `POST /api/hyperthreading` | `{"enabled": true}` |
| `GET /api/mainframe/pipeline` | Kaskade + HT-Status |

## v13.0.0 Operative + v9.10 Aspirational Modules (2026-07-15)
**Operative (v13.0.0 Kanon = v8.3 stack + Stage-A/B):** Timespace TMS, HeroicLLM-EA, Image Orchestrator, QUBO-Engine, Multi-Agent-Orchestration, Layer-Registry (13 Layers), Tailscale-Mesh + MCP, LLM Integration Hub, unified VERSION 13.0.0, consent gate, scrypt archive KDF, persona/PII gates.
**Aspirational v9.10 (AscensionOS track, partial in `ascension_os/`):** CoEvolutionaryClosure (CEC v9.3), AscensionCore (v9.4), PersistentSisyphosCycle (v9.4), HarmonisierungsCoreModule + Geisterjagdmodul (v9.6), exposure_practice_module (v9.7), GenerationalEvolutionEngine, full Inside-Out coevolution + EudaimoniaGuard extensions.
| Modul | Pfad | Features |
|---|---|---|
| Timespace TMS | `fusion_hero_os/modules/timespace_token/` | Manifold, Multi-Scale, QUBO-Hint, 3x-Fidelity, BaseModule |
| HeroicLLM-EA | `fusion_hero_os/modules/heroic_llm_ea/` | (μ+λ)-Evolution, PeerReview-Fitness, Campfire-Templates |
| Image Orchestrator | `fusion_hero_os/modules/image_orchestrator/` | 4-Stage-Pipeline, Dual-Rate-Limit, Job-Queue |
| Ascension Bridge | `ascension_os/` (via fusion_unified.yaml) | v9.10 aspirational modules (CEC, Sisyphos, Harmonisierung) — loadable, not yet operative Kanon |

## API-Endpunkte (Auswahl)
| Endpoint | Funktion |
|---|---|
| `GET /api/health` | Gesamtstatus |
| `POST /api/load-all` | Module + Agenten laden |
| `GET /api/modules` | Modul-Registry |
| `GET /api/grok/status` | Grok-intern Bridge |
| `POST /api/grok/chat` | Intent + Systemaktionen |
| `POST /api/input` | Eingabe-Layer → `job_id` |
| `GET /api/jobs/{id}` | Worker-Ergebnis |

## Agent-Kontext (Repo)
- Index: `docs/agent_context/claude_memory/MEMORY.md`
- Code-Honesty-Audit: `pending-code-honesty-audit.md`
- Hintergrund-Git: `repo-background-automation.md` — **auto_save.ps1 pausieren vor manuellem Git**

## C↔Python IPC Bridge (v1.1)
- **TCP Server (Windows):** `kernel/bridge/fhos_ipc_server.py` → `127.0.0.1:19753`
- **C Server (Linux/WSL):** `kernel/bridge/fhos_ipc_server.c` → AF_UNIX
- **Launcher:** `python start_fusion_hero.py --with-dashboard`
- **API:** `GET /api/bridge/ipc/status`, `POST /api/bridge/ipc/dispatch`
- **Fallback:** in-process wenn kein Server läuft (ehrlich gelabelt)

## Rust Workspace
- Root: `Cargo.toml` (Workspace)
- Crates: `pms_rust_kernel_crate/`, `rust_engine_crate/`
- CI: `cargo build --workspace` auf main/develop

## Grok Intern Abgleich (Session-Start) — v13.0.0 Update 2026-07-15
1. `git pull origin main` — Tag/Release `v13.0.0` ist operativer Kanon
2. `powershell -File sync_grok_intern.ps1`
3. `GET http://127.0.0.1:8000/api/health` (oder `?light=true` unter Last)
4. Falls offline: `start_all.ps1` (Fast-Boot: `FUSION_AUTO_LOAD=0`)
5. Ascension activation: `ascension_os/` Layer per `fusion_unified.yaml`
6. Referenz: `BEST_VERSION.md` (v13.0.0), `DEPLOYMENT_GUIDE.md`, `BRANCH_STRATEGY.md`, `docs/v8/`, `ascension_os/`
7. Version gate: `python scripts/bump_version.py --check` → muss `13.0.0` sein

## Code-Honesty Regel
- Docstrings/Header: nur behaupten, was der Code einlöst
- Connectors/Image-Pipeline: Dry-Run default (`would_execute=False`)
- Demo-WebSocket-Events im Dashboard sind **keine** echte Peer-Review-Logik