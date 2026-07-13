---
name: github-repos
description: Where the canonical Fusion Hero OS / ALTE_FRAU_95g code lives on GitHub and which repo holds what
metadata: 
  node_type: memory
  type: reference
  originSessionId: 20c4796a-2f0f-4c98-b165-c68f12f07795
---

The user's GitHub account is **95guknow** (gh CLI is authenticated as this account on this machine). Relevant repos (as of 2026-06-28):

- **fusion-hero-os** (Python, most recently pushed) — canonical monorepo. Notable: `03_Code/Dashboard/app.py` is a **FastAPI "Denkprozess Monitor" v5.3** with live metrics (`/api/metrics` via psutil: cpu/ram/ops-per-sec/cache-hit-rate), a WebSocket event stream (`/ws`), and a QUBO solve endpoint (`/api/qubo/solve`, same simulated-annealing engine as the local mainframe). `03_Code/Dashboard/workspace.py` is a NiceGUI app using `ui.monaco` + a monitoring column.
- **Fusion_Hero_OS_v1.1** (Python), **dashboard** (HTML), **mister-Contributor-gui** (JS), **kilo**, **heroic-fusion-os-manifest** (fork).

The local project `ALTE_Frau_95g_Core_v3.6` is a NiceGUI editor/IDE ([[gui-architecture]] if created). When asked to "look at the new features on GitHub", they mean these repos — diff against the local copy. Use `gh api repos/95guknow/<repo>/...` to inspect.
