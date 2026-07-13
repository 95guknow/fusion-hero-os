# Cross-Repo Alignment v7.5

**Date**: 2026-07-01  
**Between**: `95guknow/fusion-hero-os` (Fusion-Hero-OS v7.5 Master Unified) and `tz-dev/PMS-RUST` (PMS Evidence Spine v0.1)

> **Ehrlicher Status (2026-07-02):** Dieses Dokument beschreibt ein
> Alignment auf KONZEPT-Ebene. In diesem Repo ist von PMS-RUST nichts
> integriert (kein Code, kein Submodule, keine `PMS.yaml`), und
> "hyper-threading" bezeichnet die Simulations-Variante
> (`VirtualGPUHTCache`) — Details in `docs/01_vision/V8_STATUS_REPORT.md`.
> Hinweis: Es existiert eine abweichende Kopie unter
> `docs/03_integration/CROSS_REPO_ALIGNMENT_v7.5.md`.

## Summary

The two primary repositories have been aligned at the architectural level:

- `fusion-hero-os` provides the unified heroic core, MasterSeed, hyper-threading, governance, and high-level theory (Eudaimonismus / Heroismus).
- `PMS-RUST` provides the deterministic Δ–Ψ praxeological execution kernel with model validation and auditability.

In v7.5, the PMS Evidence Spine has been integrated as a **native first-class execution layer** inside Fusion-Hero-OS.

## Key Alignment Points

- PMS Operator Chains are now validatable output format for praxeological recommendations.
- Trust boundary from PMS-RUST is adopted (AI proposes → Host validates → Kernel executes).
- MasterSeed Strict Contraction + Hyper-Threading principles apply to PMS-integrated operations.
- Future merges between the two repos follow the v7.5 Governance rules defined in `FUSION_HERO_OS_v7.5_MASTER_UNIFIED.md`.

## Status

Alignment complete and documented. No open issues or error reports found in either repository related to this integration.

This document serves as the official cross-repo reference for v7.5.