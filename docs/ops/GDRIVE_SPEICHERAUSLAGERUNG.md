# Speicherauslagerung auf Google Drive

**Stand:** 2026-07-26 · Platform v13.0.0  
**Ziel:** C: entlasten; Cold Storage + Runtime-HT-Spill auf GDrive.

## Pfade (kanonisch)

| Rolle | Pfad |
|--------|------|
| Library | `G:\Meine Ablage` |
| Cold Offload | `G:\Meine Ablage\FusionHero_Offload` |
| Runtime spill (HT) | `G:\Meine Ablage\FusionHero_Offload\LongTermCache` |
| Medienserver mirror | `G:\Meine Ablage\Fusion_Hero_OS_v1.2` |

Env (auch `~/.fusion/gdrive_spill.env`):

```text
FUSION_GDRIVE_OFFLOAD=G:\Meine Ablage\FusionHero_Offload
FUSION_SSD_LONGTERM_CACHE=G:\Meine Ablage\FusionHero_Offload\LongTermCache
FUSION_MEMORY_SPILL=1
```

## Zwei Ebenen

1. **Disk cold offload** — `tools/disk_dedup_offload.py` / `workstation/offload-to-gdrive.ps1`  
   Installer, Archive, SD/LLM-Modelle, Grok-Sessions → `FusionHero_Offload` (copy+verify+delete).
2. **Runtime memory spill** — `SSDLongTermCache` / VirtualGPUHT  
   VRAM/RAM-Overflow → `.npy` auf LongTermCache (GDrive).

Policy: `workstation/storage_policy.json` · Resolver: `tools/storage_policy.py`.

## Befehle

```powershell
$env:FUSION_GDRIVE_OFFLOAD = "G:\Meine Ablage\FusionHero_Offload"
$env:FUSION_SSD_LONGTERM_CACHE = "G:\Meine Ablage\FusionHero_Offload\LongTermCache"
$env:FUSION_MEMORY_SPILL = "1"

# Plan
python tools\disk_dedup_offload.py --offload-plan --offload-min-mb 50

# Ausführen (Dateien + Ordner)
python tools\disk_dedup_offload.py --offload-folders --offload-execute --offload-min-mb 50 `
  --offload-dest $env:FUSION_GDRIVE_OFFLOAD

# Oder Sweep-Skript
powershell -File workstation\offload-to-gdrive.ps1 -MinMb 50
```

## Limits (ehrlich)

- GDrive/DriveFS kann **ENOSPC** melden (Cloud-Quota oder lokaler Cache voll) — dann schlagen Kopien fehl, Originale bleiben.
- Nach erfolgreichem Upload: im Explorer `FusionHero_Offload` → **Speicherplatz freigeben** (Online-only), damit C: und ggf. Drive-Cache entlastet werden.
- Secrets werden nicht ausgelagert (Policy + SAFE_EXCLUDE).

## Geltung

- Pfade + Policy + Spill-Wiring: **Satz** (im Repo/Code).
- Einzelner Offload-Lauf: **Bedingt** (Quota/I/O).
