# Cross-Repo Alignment v7.5

**Version:** v7.5  
**Status:** Konzept-Abgleich (nicht implementiert)

Dieses Dokument beschreibt den Abgleich zwischen `fusion-hero-os` und `tz-dev/PMS-RUST`.

> **Ehrlicher Status (2026-07-02):** Der Abgleich existiert auf Konzept-Ebene.
> In diesem Repo ist von PMS-RUST nichts integriert (kein Code, kein Submodule,
> keine `PMS.yaml`); "Hyper-Threading" bezeichnet die Simulations-Variante —
> Details in `docs/01_vision/V8_STATUS_REPORT.md`.

---

## Zusammenfassung

- `fusion-hero-os` liefert den unified Heroic Core + Hyper-Threading (Simulation, s. o.) + Governance.
- `PMS-RUST` liefert (konzeptionell) den deterministischen Δ–Ψ Execution Kernel — in diesem Repo NICHT vorhanden.
- Der PMS Evidence Spine ist als Execution Layer **geplant, aber NICHT integriert** (kein Kernel-Binary, keine `PMS.yaml`; jeder Aufruf endet FAIL_CLOSED). Die frühere Formulierung "ab v7.5 als native Execution Layer integriert" war eine Überclaim.

---

**Dieses Dokument gehört in die 03_integration Schicht.**