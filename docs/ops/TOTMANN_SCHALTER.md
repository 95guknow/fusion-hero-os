# Totmannschalter — 24h, dann invers-logarithmisch ausphasen

> **Stand:** v1.0.0 · 2026-08-16
> **Config:** `totmann_schalter.yaml`
> **Code:** `fusion_hero_os/core/totmann_schalter.py`
> **State:** `~/.fusion/totmann/` (operator-local, not public)

## Standard (gesetzt 2026-08-16)

| Spur | Start (jetzt) | Ziel / Streamlining | Horizont |
|---|---|---|---|
| Soft (Totmann-Ping) | **24 Stunden** | **1 Check / Monat** | 2027-12-31 |
| Hard (Präsenz) | Periode 365 Tage | **1 Check / Jahr in Schwarzkollm** | 2027-12-31 |

Nach dem Horizont bleiben die Zielraten stehen. Sie werden nicht weiter gestreckt.

## Inverse logarithmische Phasen

Das Soft-Intervall wächst log-linear im Fortschritt \(u \in [0,1]\):

\[
i(u) = i_0 \cdot \left(\frac{i_1}{i_0}\right)^{u}
\qquad
i_0 = 24\,\mathrm{h},\; i_1 = 30\,\mathrm{d}
\]

Acht Phasen, dieselbe Kurve an \(k/(N-1)\):

| Phase | \(u\) | Intervall |
|---|---|---|
| 0 | 0 | 24 h |
| 1 | 1/7 | ≈ 39.0 h |
| 2 | 2/7 | ≈ 2.6 d |
| 3 | 3/7 | ≈ 4.3 d |
| 4 | 4/7 | ≈ 7.0 d |
| 5 | 5/7 | ≈ 11.4 d |
| 6 | 6/7 | ≈ 18.5 d |
| 7 | 1 | 30 d |

## Was ein Trip tut — und was nicht

**Tut:** `state.tripped = true`, Alert unter `~/.fusion/alerts/totmann_schalter.json`, Zeile in `log.jsonl`.

**Tut nicht:** Wipe, Git-Push, Anruf, Nachricht an Dritte, stilles Zurücksetzen durch einen verspäteten Ping. Ein Trip braucht `--reset-trip`.

Der Hard-Check ist **Operator-Selbstattest** am öffentlichen Ortsnamen Schwarzkollm. Dieses Modul hat kein GPS.

## CLI

```powershell
cd C:\Users\Admin\fusion-hero-os
$env:PYTHONPATH = (Get-Location)
python -m fusion_hero_os.core.totmann_schalter --arm
python -m fusion_hero_os.core.totmann_schalter --ping
python -m fusion_hero_os.core.totmann_schalter --hard-check --site Schwarzkollm
python -m fusion_hero_os.core.totmann_schalter --status
python -m fusion_hero_os.core.totmann_schalter --evaluate
python -m fusion_hero_os.core.totmann_schalter --reset-trip
python -m fusion_hero_os.core.totmann_schalter --phases
```

## Windows-Task

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install_totmann_task.ps1
```

Stündliche Auswertung reicht, solange das Soft-Intervall ≥ 24 h ist.

## Geltung

Intervall-Mathematik und Trip-Datei = **Satz** (`proof_registry.yaml`, pytest).
„Blockiert Merges / löscht Daten / ruft an“ = **nicht beansprucht**.
