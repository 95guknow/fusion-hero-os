# fusion-hero-os

**Status:** v8 (Doku/Struktur konsolidiert; Kernfunktionalität teilweise/aspirational)  
**Hyper-Threading:** `VirtualGPUHTCache` ist Simulation; echte verifizierte Mehrkern-Parallelisierung separat in `engine/mainframe.py` (numba nogil + ThreadPoolExecutor)  
**Mathematische Fundierung:** Heroic Math Engine integriert, aber nicht abgeschlossen (Knoten 16 = Fragment, 19 = Modell mit ~29 % Monotonie-Verletzungen im Sweep, 17/20 nicht implementiert)

Ein heroic Framework für Rekonstruktivistischen Eudaimonismus und maximale intellektuelle Präzision.

## Aktueller Stand
- Version: v8 (Fusion Hero OS + OptimizerInsights Consolidation)
- **Hyperthreading:** echt und gemessen — `parallel_anneal(backend="auto")` in
  `fusion_hero_os/engine/` nutzt Rust/rayon (~4.4x) bzw. Numba-nogil (~3.4x)
  über alle logischen Kerne; `VirtualGPUHTCache` (03_Code) ist davon getrennt
  eine Simulation
- **Mathematischer Kern:** Knoten 16/17/19/20 als bewiesene Sätze
  (`fusion_hero_os/core/heroic_math_engine.py` — Beweise + 0-Verletzungs-Sweeps
  + Regressionstests); PMS Evidence Spine: eigener deterministischer Minimal-Kernel `pms_rust_kernel` implementiert (2026-07-04): PMS.yaml-Validierung, JSONL-Audit, FAIL_CLOSED; Operatoren = die vier bewiesenen Knoten-Saetze. Das externe tz-dev/PMS-RUST bleibt NICHT eingebunden
  (siehe `docs/01_vision/V8_STATUS_REPORT.md`)
- MasterSeed: M_0'''' — `verify_integrity()` ist seit 2026-07-04 eine ECHTE Pruefung
  (SHA-256-Zustands-Hash + Kontraktions-Check); MasterSeed-Syncs optimieren sich
  BEWEISBAR gegenseitig (`fusion_hero_os/core/masterseed_sync.py`, Satz + Tests)
- Struktur: siehe [docs/v8/PROJECT_STRUCTURE_v8.md](docs/v8/PROJECT_STRUCTURE_v8.md)
- Branches: siehe [docs/v8/BRANCH_STRATEGY_v8.md](docs/v8/BRANCH_STRATEGY_v8.md)
- CI: `ci.yml` + `fusion-hero-os-hyperthread.yml` (grün auf `main`); redundante/kaputte Workflows entfernt

Es bietet eine klare Top-Down-Dokumentationsarchitektur (real fertiggestellt); die mathematische Strenge ist erklärtes Ziel, nicht erreichter Stand — siehe `docs/01_vision/V8_STATUS_REPORT.md`.

## Aktueller Stand (v8)

- Neue Top-Down-Dokumentationsstruktur (`01_vision/` bis `99_archive/`) — real und verifiziert
- `core/heroic_math_engine.py` – läuft mit echten Asserts (`tests/test_heroic_math_engine.py`); die frühere Behauptung "Knoten 16–20 repariert" war eine Überclaim und ist zurückgenommen
- Core-Python-Module mit v8-Headern versehen (kosmetisch, kein funktionales Rework)
- `modules/` neu strukturiert — `alte_frau_95g/`, `mainframe_laden/`, `skill_creator/` sind derzeit leere Platzhalter

Siehe `docs/OVERVIEW.md` für die vollständige Struktur.
