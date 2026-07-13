---
name: project-architecture
description: Module layout of the local Fusion Hero OS / ALTE_FRAU_95g project and key design constraints
metadata: 
  node_type: memory
  type: project
  originSessionId: 20c4796a-2f0f-4c98-b165-c68f12f07795
---

**2026-06-29 — `main` switched to the canonical monorepo.** Local `main` now tracks `fusion-hero-os/main` (remote `fusion-hero-os`, was 80 commits ahead of an UNRELATED local history — no common ancestor). Top-level layout of the new `main` is the flat monorepo: `01_Framework`, `02_Mathematik`, `03_Code`, `04_Buch_und_Archiv`, `06_Master_Archive`, `kernel/`, `qb_qubo.py`, many `*.md`/`*.ps1`/`*.bat`. **The Python-package project described below (app.py / engine / orchestration / methodology / rust_engine_crate) is NO LONGER on `main`** — it is preserved verbatim on branch `backup/local-main-pre-sync` (`0725947`). The `claude/loving-williams-ae2943` branch (Supervisor.report fix in `orchestration/agents.py`) belongs to that backup lineage, not the monorepo. Auth: use a PAT via `$env:GH_TOKEN` + `gh auth setup-git` (do NOT pipe the token into `gh auth login --with-token` from PowerShell — it corrupts the token → false 401).

Local project (cwd `ALTE_Frau_95g_Core_v3.6`) file map after the 2026-06-28 build-out — **this layout now lives on `backup/local-main-pre-sync`, not `main`:**

- **app.py** (v2.2) — NiceGUI 3.13 IDE: splitter, file tabs+dirty tracking, run-console, 5-dim review, ZIP bundle, Mainframe dialog, live CPU/RAM. `ui.echart` charts (convergence/heatmap/metrics/sweep) + a **Pipelines panel** with 4 workflows. `REVIEW_CHECKS`/`score_review()` lifted out of `review()`. v2.2 adds a **modular Editor|Agent splitter** with a live **Hauptagent-Monitor** (Belegschaft + event stream) and a **Chat-I/O panel**, both wired to agents.py via a persistent `AGENT_BUS` + a 0.3s `refresh_live()` timer; `_run_agent_batch()` spins a Supervisor per chat message. Verify the GUI with the Claude_Preview MCP against `.claude/launch.json` (name `fusion-hero-os`, port 8080); the app uses `reload=False` so a restart + hard browser refresh is needed after edits.
- **heroic_core_mainframe.py** (v5.25) — QUBO engine. Two numba kernels: `_simulated_annealing_kernel` (single-shot, used by `simulated_annealing()`/ClassicalBackend) and `_sa_kernel_trace` (nogil, used by `parallel_anneal()`). `parallel_anneal(Q,steps,T0,n_restarts,n_samples,base_seed,workers)->dict{solution,energy,energies,best_restart,traces,trace_steps,n_restarts,workers,runtime_seconds}`. `warmup_kernels()` pre-JITs both. Hyperthreading = ThreadPoolExecutor + nogil (NOT multiprocessing; ~3.6x on 6 phys/12 logical cores).
- **core_modules.py** — methodology modules from HEROIC_SKILL.md as code: PeerReview, Erkenntnisprozess (5-stage), FormalMathematics, V3.3Structure, AutomaticArchiving (plan-only), Roadmap.
- **connectors.py** — GitHub/Drive/Vercel/Gmail/XAPI wrappers. **Constraint: NO real outward actions by default** — without an injected client every method returns a DRY-RUN plan dict (`would_execute=False`). Don't change this without explicit user opt-in.
- **agents.py** — runnable pure-Python multi-agent orchestration: MessageBus, TaskQueue, Agent (heartbeats, spawn/dismiss subagents = hire/fire), Supervisor (scales workforce up/down). Threads, terminates cleanly. No external LLM calls.
- **knowledge.py** — the session's architecture/decisions as importable data + `as_markdown()`.

GUI verification is import-build + server-200 + headless function tests; click-through is done via the Claude_Preview MCP (launch.json `fusion-hero-os`). See [[github-repos]].

**2026-06-28 reorg (v2.3):** the project was reorganized into packages (no deletions, git mv): `engine/mainframe.py` (was heroic_core_mainframe.py), `orchestration/agents.py`, `methodology/{core_modules,connectors,knowledge}.py`, `docs/{SKILL,HEROIC_SKILL}.md`; `app.py` now does `from engine import mainframe as hc` / `from orchestration import agents as ag`. Local ↔ `Fusion_Hero_OS_v1.1` are in sync with this layout (v1.1 is the canonical project repo). The `fusion-hero-os` monorepo holds a FLAT v2.2 snapshot under `03_Code/FusionHeroOS_v2.2/` (not yet reorganized).

**Hyperthreading:** `parallel_anneal` genuinely uses all cores (~3.4x, ~10/12 cores busy — verified). The live agent swarm now uses a REAL compute executor (`_cpu_task_executor` in app.py → nogil kernel) so the Hauptagent visibly loads cores; the Monitor shows "⚡ Kerne aktiv: N/12".

**Gotcha:** cloning `fusion-hero-os` on Windows fails (`exit 128`) on deeply-nested `04_Buch_und_Archiv/...` paths (>260 chars). Never `git add -A` after a partial clone — it stages phantom deletions. Use index-only ops (reset --soft) or only touch the subfolder.
