# V8 Strategy

**Version:** v8  
**Status:** Aktuell

Dieses Dokument beschreibt die Repo- und Branch-Strategie für die v8-Konsolidierungsphase.

---

## Ziel von v8

- `fusion-hero-os` als einziges aktives Entwicklungs-Repository etablieren
- Klare Trennung zwischen Strategie, Architektur und Umsetzung
- Seriöse, professionelle Repository-Struktur
- Integration des PMS Evidence Spine als Execution Layer *(Ziel — Ist-Stand 2026-07-02: NICHT implementiert, kein Kernel/keine `PMS.yaml`; siehe `docs/01_vision/V8_STATUS_REPORT.md`)*

---

## Repository-Rollen

- `fusion-hero-os`: Primary Development Repository
- `heroic-fusion-os-manifest`: Philosophisches & stilistisches Referenz-Repo
- Andere 95guknow-Repos: Legacy / Ideen-Quellen
- `tz-dev/PMS-RUST`: Technischer Execution Spine

---

## Branch-Strategie

- `main`: Stabile Version
- `v8/`: Aktive v8-Entwicklung
- `archive/`: Alte Versionen und Experimente
- `feature/`: Fokussierte Weiterentwicklungen

---

**Diese Strategie ist verbindlich für die v8-Phase.**