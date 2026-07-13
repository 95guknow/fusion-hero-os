# Fusion Hero OS v8 — Projektstruktur (Ist-Zustand)

Diese Datei beschreibt die tatsächliche, aktuelle Ordnerstruktur des Repos
(Stand: Registry-/Restrukturierungs-Durchgang 2026-07). Sie ersetzt ältere,
teils rein aspirative Struktur-Dokumente (siehe `docs/99_archive/PROJECT_STRUCTURE_v7.4.md`),
die Ordner/Dateien beschrieben, die nie umgesetzt wurden.

## Zwei parallele Systeme — wichtig zu verstehen

Das Repo enthält **zwei unabhängige Implementierungen**, die man leicht
verwechselt, weil beide "Fusion Hero OS" heißen:

1. **`fusion_hero_os/` + `app.py`** (Root) — ein schlankes, vollständig
   getestetes NiceGUI-IDE-Tool: QUBO-Solver, Multi-Agenten-Orchestrierung,
   ein paar mathematische Kernmodule. Das ist der Teil, der in `tests/`
   abgedeckt und in CI geprüft wird.
2. **`03_Code/`** — das deutlich größere, tatsächlich produktiv genutzte
   System: eine FastAPI-Dashboard-App (`03_Code/Dashboard/app.py`, gestartet
   über `run_backend.bat`/`start_all.ps1`) mit 35+ Modulen unter `03_Code/core/`
   (GPU-/CPU-Tuning, Hyperthreading, Agent-Routing, lokale LLM-Anbindung,
   Google-/Supabase-Sync, eigene Modul-Registry). Dieser Teil hat **keine**
   automatisierten Tests und wurde in diesem Durchgang nur punktuell
   angefasst (siehe unten), nicht strukturell umgebaut — dafür fehlt die
   Möglichkeit, ihn hier automatisiert zu verifizieren (GPU/LLM/Supabase
   sind zur Laufzeit nötig).

Verbindung zwischen beiden: `03_Code/core/v8_core_bridge.py` lädt
`fusion_hero_os.core.heroic_math_engine` und `...heroic_core_orchestrator`
über den normalen Python-Importmechanismus und registriert sie in
`03_Code/core/module_registry.py` unter den Namen `heroic_math_engine` /
`heroic_core_orchestrator`.

## fusion_hero_os/ — Paketstruktur

Root-level `core/`, `engine/`, `orchestration/`, `methodology/`, `modules/`
liegen jetzt gebündelt unter einem Namespace-Package, statt fünf lose
Top-Level-Ordner zu sein:

```
fusion_hero_os/
├── __init__.py
├── registry.py             # Subsystem-Registry: "ist Paket X importierbar?" (siehe unten)
├── config.py               # DispatcherConfig (max_workers, deaktivierte Module — via ENV)
├── core/
│   ├── heroic_math_engine.py, heroic_core_orchestrator.py, cec.py, rhe.py, ...
│   ├── base_module.py       # BaseModule-Vertrag: process()/propose_evolution()/peer_review()
│   └── dispatcher.py        # Dispatcher: registriert BaseModule-Instanzen, routet Anfragen
├── engine/                  # mainframe.py (QUBO/SA-Solver), mining_qubo.py, rust_backend.py
├── orchestration/           # agents.py — MessageBus, TaskQueue, Supervisor
├── methodology/             # connectors.py, core_modules.py, knowledge.py
└── modules/                 # BaseModule-Adapter (SelfModify, PeerReview, ...) + drei Platzhalter-Pakete
```

`app.py` (NiceGUI-GUI, Root-Einstiegspunkt) bezieht `engine.mainframe` und
`orchestration.agents` über die Registry statt per Direktimport.

Installierbar via `pyproject.toml`: `pip install -e ".[dev]"`.

## Dispatcher + Core-Module (BaseModule-Architektur)

Zusätzlich zur Subsystem-Registry (siehe unten) gibt es eine zweite,
komplementäre Ebene für einzelne, fachliche Core-Module:
`fusion_hero_os/core/base_module.py` definiert den Vertrag
(`process(payload)`, optional `propose_evolution(context)`,
optional `peer_review(target)`), `fusion_hero_os/core/dispatcher.py`
registriert Instanzen davon unter einem Namen und routet Anfragen dorthin
— inklusive optionaler Parallelausführung mehrerer Anfragen über
`ThreadPoolExecutor` (`Dispatcher.dispatch_many(..., parallel=True)`).

```python
from fusion_hero_os.core.dispatcher import build_default_dispatcher

dispatcher = build_default_dispatcher()
dispatcher.dispatch("PeerReviewCoreModule", {...})
```

Registrierte Module (`fusion_hero_os/modules/`, siehe `ALL_CORE_MODULES`):

| Modul | Status | Beschreibung |
|---|---|---|
| `SelfModifyCoreModule` | adaptiert | Sammelt strukturierte Verbesserungsvorschläge (`EvolutionProposal`, optional als Diff-Text). Wendet **nichts** an — jeder Vorschlag landet als `pending_review` in der Historie und muss von einem Menschen/einer CI-Pipeline normal committet werden. |
| `PeerReviewCoreModule` | neu | Code-Review-Checkliste mit 6 festen Kriterien (Korrektheit, Tests, Style, Sicherheit, Doku, Performance). Bewertet nur explizit übergebene Signale, keine automatische Code-Analyse. Zu unterscheiden von `methodology.core_modules.PeerReviewCoreModule` (Fließtext-Review, 5 Argumentationsdimensionen) — beide heißen gleich, prüfen aber unterschiedliche Dinge. |
| `FormalMathematicsCoreModule` | adaptiert | Wrapt die reale Implementierung in `methodology/core_modules.py` (Satz/Bedingt/Modell/Fragment-Klassifikation). |
| `AutomaticArchivingCoreModule` | adaptiert | Wrapt `methodology/core_modules.py` — erzeugt nur einen Archivierungs-Plan, schreibt/zippt nichts. |
| `GenerationalEvolutionProtocolCoreModule` | adaptiert | Wrapt die echte (μ+λ)-Evolutionsstrategie in `engine/mainframe.py` über QUBO-Solver-Hyperparameter — kein Stub, die Elite-Fitness ist nachweislich monoton nicht-fallend. |
| `QUBOIntegrationCoreModule` | adaptiert | Wrapt den echten, audit-gesicherten QUBO-Solver-Lauf in `engine/mainframe.py`. |
| `WeltraudaimoniaModule` | neu | Projekt-interne, gewichtete Mehrkriterien-Bewertungsheuristik für Entscheidungen (4 Achsen). Explizit dokumentiert als In-App-Heuristik ohne Anspruch auf reale ethische Autorität. |
| `MERModule` | neu | Projekt-interne "MER-Index"-Kennzahl (3 gewichtete Komponenten) plus Greedy-Priorisierung (`optimize()`), welche Komponente den größten Hebel hätte. Selbst definierte Metrik, keine externe Größe. |
| `ConversationContextCoreModule` | neu | Begrenztes In-Memory-Konversationsfenster (FIFO-Eviction). |
| `LiveProcessTrackingCoreModule` | neu | In-Memory-Status-Tracking benannter Vorgänge (start/complete/fail). |

Entwickler-Utility: `python scripts/dispatcher_status.py` zeigt die
registrierten Module ohne Testcode schreiben zu müssen.

## Zentrale Registry statt loser Verdrahtung

`fusion_hero_os/registry.py` ersetzt das frühere Muster aus drei
kopierten `try: import X except ImportError: X = None`-Blöcken in
`core/__init__.py`. Eine deklarative Tabelle (`DEFAULT_MODULES`) listet
jedes Teilsystem mit Name, Importpfad, Beschreibung und ob es
"required" ist. `Registry.get(name)` liefert entweder das geladene Modul
oder wirft `ModuleUnavailableError` mit Statusgrund — kein stilles `None`
mehr, das später an anderer Stelle zu einer nicht nachvollziehbaren
`AttributeError` führt. Wichtig: ein echter Bug im Modul (Status `failed`)
wird von einer fehlenden optionalen Abhängigkeit (Status `unavailable`)
unterschieden statt beides gleich zu behandeln.

Statusüberblick: `python -m fusion_hero_os.registry`.

`03_Code/core/module_registry.py` ist die (deutlich größere) Registry des
produktiven Systems — strukturell ähnliches Muster (deklarative Registrierung,
`load_all()`/`load_module()`/`list_modules()`), aber mit eigener Historie.
In diesem Durchgang wurde dort nur die Fehlerbehandlung geschärft (echte
Bugs werden jetzt geloggt statt still im selben `except Exception` wie
fehlende Dependencies zu verschwinden) und ein hartkodierter, maschinenspezifischer
Pfad (`C:\Users\Admin\heroic-highest-layer`) durch `Path.home()` +
`FUSION_HIGHEST_LAYER_PATH`-Override ersetzt. Eine vollständige
Zusammenführung beider Registries stand nicht im Scope dieses Durchgangs.

## Weiterer aktiver Code

| Pfad | Sprache | Zweck |
|---|---|---|
| `src/` | JS/Svelte | SvelteKit-Frontend (eigenständig, kommuniziert nicht direkt mit dem Python-Kern im Code) |
| `rust_engine_crate/` | Rust | PyO3-Bindings für den Solver-Kernel (experimentell, noch nicht produktiv eingebunden) |
| `kernel/` | C/ASM | Low-Level-Prototyp (Boot-Code, Treiber-Stubs) — experimentell, nicht Teil des laufenden Systems |
| `tests/` | Python | pytest-Suite für `fusion_hero_os/` (inkl. `test_registry.py`, `test_dispatcher.py`), von CI ausgeführt |
| `scripts/` | Python | Entwickler-Utilities, z.B. `dispatcher_status.py` (Registrierungsstatus ohne Testcode) |

## Konfiguration & Tooling

- `pyproject.toml` — Paket-Metadaten, Dependencies, pytest- und ruff-Konfiguration (ersetzt die vorherigen `requirements.txt`/`requirements-dev.txt`/`pytest.ini`)
- `package.json` / `vite.config.js` / `jsconfig.json` — Node/SvelteKit-Toolchain
- `.github/workflows/` — CI (siehe unten)
- `Dockerfile` — Container-Build

## CI-Workflows

- `ci.yml` — Haupt-CI: Ruff-Lint über `fusion_hero_os/`, Heroic-Math-Engine-Verifikation, Registry-Statusbericht, pytest (Matrix: Python 3.11/3.12 auf `main`/`develop`, leichter Check auf anderen Branches)
- `fusion-hero-os-hyperthread.yml` — Strukturvalidierung (`fusion_hero_os/core` vorhanden, Python-Syntax-Check über das ganze Paket, Migrationskonzept-Vollständigkeit)
- `summary.yml` — automatische Zusammenfassung neuer Issues

## Dokumentation & Archiv

- `docs/` — aktive Dokumentation (Architektur, Integration, Roadmap)
- `docs/99_archive/` — historische/versionierte Markdown-Dokumente (v7.4–v7.12), aus dem Root hierher verschoben
- `04_Buch_und_Archiv/`, `06_Master_Archive/`, `archive/`, `v2_beta/` — größere historische Materialsammlungen (Buch-Manuskripte, alte Framework-Stände). Nicht inhaltlich konsolidiert — erfordert Bewertung durch den Repo-Owner.

## Bekannte offene Punkte

- `src/` (SvelteKit) und `fusion_hero_os/` laufen unabhängig; eine dokumentierte Schnittstelle (REST/WebSocket) fehlt.
- `rust_engine_crate/` ist nicht in `fusion_hero_os/engine/rust_backend.py` eingebunden (Stub).
- `03_Code/` (das eigentlich produktiv genutzte, größere System) ist strukturell nicht mit `fusion_hero_os/` vereinheitlicht — nur einseitig über `v8_core_bridge.py` angebunden. Eine echte Zusammenführung beider Registries wäre der nächste sinnvolle Schritt, erfordert aber Entscheidungen, die über automatisierte Refactorings hinausgehen (z. B. ob `03_Code/` mittelfristig in `fusion_hero_os/` aufgehen soll).
- Mehrere Ordner enthalten Mehrfachversionen desselben Inhalts (z. B. `03_Code/core/knowledge/Geisteskrankheiten_4D_Matrix_v2` bis `v7`, dreifach verschachtelte Kopien in `04_Buch_und_Archiv/`). Konsolidierung erfordert inhaltliche Entscheidungen und wurde bewusst nicht automatisiert durchgeführt.
