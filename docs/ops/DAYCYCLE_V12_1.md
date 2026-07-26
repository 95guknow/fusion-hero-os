# Daycycle + Zentralkonsolidierung v12.1.0

**Platform:** Fusion Hero OS **12.1.0**  
**Config:** `daycycle_mem.yaml`  
**Code:** `fusion_hero_os/core/daycycle_mem.py`  
**Private mem repo:** `95guknow/fusion-hero-os-daily-plans` (private)  
**Public kanon:** `95guknow/fusion-hero-os` (code only — **no mem content**)

## Tagesablauf

| Takt | Aktion | Ziel |
|------|--------|------|
| **1 min** | Zeile in lokale `mem.md` | `~/.fusion/daycycle/mem.md` |
| **1 h** | Flush: commit+push, dann **leeren** | private repo branch **`dev`** |
| **4 h** | PR `dev` → `main` | private repo |
| **1×/Tag (03:00)** | Merge top + Fan-out Pull | private `main` → alle Instanzen |

## Agent-Protokoll

- **Default:** nur protokollieren (`~/.fusion/daycycle/agent_protocol.jsonl`)
- **Wake word:** `testtest` → aktive Engagement-Fenster (TTL 30 min, konfigurierbar)
- Echtwelt-Traffic der Instanzen: normales Logging in `instance_traffic.jsonl` — Agent greift **nicht** ein, außer nach Wake

## CLI

```powershell
cd C:\Users\Admin\fusion-hero-os
$env:PYTHONPATH = (Get-Location)
python -m fusion_hero_os.core.daycycle_mem --status
python -m fusion_hero_os.core.daycycle_mem --minute
python -m fusion_hero_os.core.daycycle_mem --hourly
python -m fusion_hero_os.core.daycycle_mem --pr
python -m fusion_hero_os.core.daycycle_mem --daily
python -m fusion_hero_os.core.daycycle_mem --due
python -m fusion_hero_os.core.daycycle_mem --all   # force full cycle once
```

## Tasks installieren

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_daycycle_tasks.ps1
```

## Bottom-up Upgrade v12.1

1. `python scripts/bump_version.py 12.1.0` (Manifeste)
2. Daycycle engine + mem private path
3. Quantize selfmod, virtual timelines, dual-org (bereits in 12.0.x Stack)
4. Fan-out: `python -m fusion_hero_os.core.daycycle_mem --fanout`

## Bounds

- Mem **nie** in public `fusion-hero-os`
- Keine Vault-Secrets in mem (Redaction)
- Offense FORBIDDEN
- PR/Merge nur private daily-plans

## Geltung

Minute-Zeilen / git Results = **Satz**. Schedule-Sprache = **Spezifikation**. Manigfaltigkeit = **Modell**.
