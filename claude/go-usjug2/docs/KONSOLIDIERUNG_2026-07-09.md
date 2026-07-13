# Konsolidierung 2026-07-09 — Top-down/Bottom-up-Korrelation

Repo `fusion-hero-os` einmal auf konsistenten Stand gebracht: Top-down-Analyse
(Struktur, CI, Datei-Typen) mit einer Bottom-up-Analyse (jede JSON-/YAML-/
Python-Datei geparst) korreliert. Behoben wurden ausschließlich Defekte, die ein
Parser/CI hart bricht — keine inhaltlichen Umformulierungen.

## Behobene Befunde

### 1. Nicht aufgelöste Git-Merge-Konflikte (3 JSON-Dateien)
`03_Code/core/knowledge/geisteskrankheiten_4d_v2.json`, `…_v4.json`, `…_v5.json`
enthielten je einen unaufgelösten Konflikt (`<<<<<<< HEAD … ======= … >>>>>>>`)
aus dem Auto-Save-Commit `1e9b21f` (2026-07-09_05-50-13). Dadurch war die JSON
ungültig und für jeden `json.load` unbrauchbar.

Der Konflikt betraf jeweils nur das Feld `updated_ts`. **Datumsbasiert
aufgelöst** — der neuere Zeitstempel (eingehende Seite, `1783568998.*`) gewinnt
gegenüber der älteren HEAD-Seite (`1783178702.*`). Alle drei Dateien parsen jetzt.

### 2. UTF-8-BOM in Python-Dateien (5 Dateien)
Ein führendes Byte-Order-Mark (`U+FEFF`) ließ diese Dateien mit
`invalid non-printable character` scheitern:
- `03_Code/core/__init__.py`
- `03_Code/suite/audio-bridge/bridge.py`
- `03_Code/suite/audio-bridge/test_tone.py`
- `legacy_sources/private-hacking-suite/audio-bridge/bridge.py`
- `legacy_sources/private-hacking-suite/audio-bridge/test_tone.py`

BOM entfernt; alle 524 Python-Dateien des Repos parsen jetzt fehlerfrei.

### 3. Ungültige CI-Workflow-YAML (2 Dateien)
`.github/workflows/fusion-hero-os-ci-v8.yml` und
`.github/workflows/Fusion-Hero-OS_CI_v8_FUsion_branch_resolved.yml` betteten
Python über mehrzeilige `python -c "…"`-Blöcke ein, deren Code auf Spalte 0
stand. Damit endete der YAML-Block-Scalar vorzeitig und die Workflow-Datei war
ungültig — GitHub lehnt eine solche Datei komplett ab.

Auf **Einzeiler** umgestellt (identische Kommandos, gleiches Verhalten) — genau
das Muster, das dieselbe Datei an anderer Stelle bereits verwendet. Alle 5
Workflows parsen jetzt als gültige YAML.

## Bewusst nicht geändert

- `jsconfig.json` meldet der strikte JSON-Parser als „ungültig", ist aber
  korrektes **JSONC** (Kommentare erlaubt für `jsconfig`/`tsconfig`) — kein Fehler.
- Große Build-Artefakte im Repo (`*.exe`, PyInstaller-`build/`-Bäume unter
  `04_Buch_und_Archiv/…`, `hallo.pdf`) blähen jeden Clone auf ~91 MB. Empfehlung:
  aus der Versionskontrolle nehmen und über `.gitignore` ausschließen. Nicht
  entfernt, da möglicherweise als Release-Beilage gewollt.
- `.env` ist korrekt **nicht** getrackt; `.env.example` enthält nur leere
  Platzhalter. Keine echten Secrets im Repo gefunden.
