# v12.1.0 — Zentralkonsolidierung · volle Mannigfaltigkeit · bottom-up

**Stand:** 2026-07-21  
**Upgrade:** 12.0.0 → **12.1.0** (additiv, BCG)

## Was v12.1 hinzufügt

| Layer | Inhalt |
|-------|--------|
| L0 | Daycycle state + agent wake protocol (`testtest`) |
| L1 | Minute mem.md + instance traffic jsonl |
| L2 | Hourly private `dev` flush (daily-plans) |
| L3 | 4h PR + daily top merge + fan-out |
| L4 | Docs / scheduled tasks / public-safe summaries only |

## Instanzen (Fan-out)

Siehe `daycycle_mem.yaml` → `instances[]`. Fehlende optionale Pfade werden übersprungen.

## Nicht Teil des public mem-Push

Vault · `.env` · GPG shards · Klartext-Secrets

## Operator-Hinweis

Ab jetzt läuft der Tageablauf im Minutentakt in **lokaler** `mem.md`.  
Agent greift **nur** bei explizitem **`testtest`** ein; sonst reines Protokoll.
