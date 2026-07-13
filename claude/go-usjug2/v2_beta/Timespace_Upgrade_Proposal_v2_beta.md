# Timespace Upgrade Proposal (v2_beta)

**Status:** Scaffold implementiert in `03_Code/timespace_token_management.py` (2026-07-05).
Volle Zeitaum-Geometrie aus Grok-Projekten war nicht exportierbar — dieses Dokument
ersetzt den Ein-Zeilen-Platzhalter ehrlich.

## Ziel

Token-Budgets nicht nur nach Kosten (TMS v1.0), sondern nach **Zeit-Raum-Position**
im evolutionären Stack verteilen: Layer-0-Nähe = höhere Priorität; entfernte
Meme-/Sisyphos-Tracks werden bei Knappheit geometrisch komprimiert.

## Implementiert (vertieft 2026-07-05)

- `TimespaceManifold` — Layer-Ursprünge + Multi-Scale (`micro`/`meso`/`macro`)
- `TimespaceTokenManager.allocate_with_report()` — voller Allokations-Report
- QUBO-Hint: `build_competition_qubo` + `greedy_bottleneck_assignment` + Energie-Metrik
- 3×-Fidelity für Meme/Coevolution nahe Layer-Ursprung
- Nachbarschafts-Kompression bei dichten Tracks
- `TimespaceTokenCoreModule` (BaseModule + Dispatcher)

## Offen (Konzept)

- Volle Zeitaum-Manifold-Geometrie (>2D, gekrümmt)
- Echter QUBO-Solver (qb_qubo/parallel_anneal) statt Greedy-Hint

## Code-Honesty

| Teil | Status |
|------|--------|
| TMS v1.0 Basis | Implementiert (`03_Code/TokenManagementSystem.py`) |
| Geometrische Erweiterung | Minimal-Scaffold (`timespace_token_management.py`) |
| Volle v2_beta-Vision | Konzept — kein Grok-Export eingegangen |