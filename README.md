# Fusion Hero OS — ALTE_FRAU_95g Core

Ein lokaler QUBO-Solver-Mainframe mit NiceGUI-IDE, paralleler Multi-Core-Engine
und einem live beobachtbaren Multi-Agenten-System.

## Schnellstart

```bash
pip install -r requirements.txt
python app.py            # öffnet die GUI auf http://localhost:8080
```

> Hinweis: Die GUI läuft mit `reload=False`. Nach Code-Änderungen den Prozess
> neu starten und den Browser-Tab hart neu laden (Strg+F5).

## Projektstruktur

```
app.py                     GUI-Einstiegspunkt (NiceGUI 3.13): Editor, Pipelines,
                           Charts, Live-Hauptagent-Monitor + Chat
engine/
  mainframe.py             QUBO-Engine: Simulated Annealing (numba),
                           parallel_anneal() — Multi-Start über alle Kerne
                           (nogil + ThreadPoolExecutor), Audit-Layer (Layer 1/3)
orchestration/
  agents.py                Pure-Python Multi-Agenten-Orchestrierung:
                           MessageBus, Supervisor (hire/fire), Worker-Threads
methodology/
  core_modules.py          Methodik als Code: PeerReview, Erkenntnisprozess,
                           FormalMathematics, V3.3-Struktur, Archivierung, Roadmap
  connectors.py            Konnektoren (GitHub/Drive/Vercel/Gmail/XAPI) —
                           DRY-RUN per Default, keine echten Außenaktionen
  knowledge.py             Architektur-/Entscheidungs-Wissensbasis als Daten
docs/
  SKILL.md                 Methodik-Referenz (vollständig)
  HEROIC_SKILL.md          Methodik-Referenz (neutrale Fassung)
```

## Kernkomponenten

### Engine — `engine/mainframe.py`
- `simulated_annealing(Q, steps, T0)` — Einzellauf (jitted Kernel).
- `parallel_anneal(Q, steps, T0, n_restarts, n_samples)` — **Hyperthreading**:
  `n_restarts` unabhängige Läufe laufen parallel über alle logischen Kerne
  (numba `nogil` gibt den GIL frei), beste Lösung gewinnt; liefert Konvergenz-Traces.
- `QUBOIntegrationCoreModule` — Orchestrierung mit Pre-/Post-Solve-Audit.

### GUI — `app.py`
- Editor mit Tabs, Datei-Filter, 5-Dimensionen-Review, ZIP-Archivierung.
- **Pipelines**: Erkenntnis-Lauf (5 Stufen), Parallel-Solve & Visualize,
  Active-File Review & Archive, Sweep & Compare.
- **Visualisierung** via ECharts: Konvergenz, Q-/Beitrags-Heatmap, CPU/RAM-Verlauf, Sweep.
- **Hauptagent-Panel**: Live-Monitor (Belegschaft, Ereignis-Stream, aktive Kerne)
  und Chat-I/O — gibt dem Schwarm echte CPU-Aufgaben (sichtbare Mehrkern-Last).

### Agenten — `orchestration/agents.py`
- `Supervisor` skaliert die Belegschaft dynamisch hoch/runter, verteilt Tasks,
  aggregiert Status. Worker führen einen pluggable Executor aus (Default: simuliert;
  in der GUI: echter QUBO-Compute → nutzt Hyperthreading).

## Abhängigkeiten
`nicegui>=3.0`, `numpy`, `numba`, `psutil` (siehe `requirements.txt`).
