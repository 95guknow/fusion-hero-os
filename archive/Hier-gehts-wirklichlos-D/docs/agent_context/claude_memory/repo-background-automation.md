---
name: repo-background-automation
description: "The fusion-hero-os working copy runs background scripts that auto-commit, switch branches, and merge — racing with manual git work"
metadata: 
  node_type: memory
  type: project
  originSessionId: c2046e22-d58d-4841-9164-29846cd96707
---

Observed 2026-06-29 in cwd `ALTE_Frau_95g_Core_v3.6`: during manual git work, the working tree was repeatedly committed and the checkout switched (`main` ↔ `v2-beta`), with merge commits appearing **between tool calls** and no manual action. E.g. dashboard files (`supabase_client.py`, `requirements.txt`, `app.py`) that were uncommitted one moment showed up as commit `7a023f0` on `main` (and merged into `v2-beta` as `b51b118`) the next.

Likely cause: top-level scripts in the repo — `auto_save.ps1`, `end_session.ps1`, `sync_grok_intern.ps1`, `sync_medienserver.ps1`.

**How to apply:** Before any manual commit/push, expect the tree to move under you. Pause these scripts first, or re-check `git status` immediately before acting — "commit the working tree changes" is a moving target otherwise. Race can cause confusing empty diffs, unexpected branch (`v2-beta`) checkouts, and surprise merges/conflicts.

Branch policy (from commit history): maintainer-direct-to-main from PC; all other commits → `v2-beta`, then PR to `main`. See [[project-architecture]].
