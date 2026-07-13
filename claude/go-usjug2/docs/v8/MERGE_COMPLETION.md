# Bottom-Up Merge Completion (v8/bestversion)

**Date:** 2026-07-06  
**Status:** Complete — suite modules integrated into `03_Code/core/`

## Canonical Core Modules (new)

| Module | Role |
|--------|------|
| `core/qb_qubo.py` | Re-export shim → `03_Code/tools/qb_qubo.py` |
| `core/ghosthunt_hook.py` | Geisterjagd + springloop coevolution hook |
| `core/suite_pipeline.py` | Programmatic 8-layer COEVO runner |
| `core/suite_bridge.py` | Suite inventory, GPU probe, fusion health |

## Orchestration Integration

- `heroic_orchestration.auto_load()` now loads `suite_bridge` status
- `heroic_orchestration.apply_ghosthunt_coevo()` for layer hooks
- `create_classified_task()` attaches `coevo` state on QUBO tasks

## API Endpoints (Dashboard)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/suite/status` | GET | Full suite + GPU + fusion health |
| `/api/suite/pipeline/status` | GET | Layer inventory without running |
| `/api/suite/pipeline/run` | POST | Run full 8-layer COEVO pipeline |
| `/api/suite/ghosthunt` | POST | Single ghosthunt hook probe |

## Suite Delegates to Core

- `03_Code/suite/ghosthunting/hook.py` → `core.ghosthunt_hook`
- `03_Code/suite/process_layers.py` → `core.suite_pipeline.run_full_pipeline`

## Tests

```bash
python -m pytest tests/test_suite_integration.py -q
```

## Next evolution (optional)

- Merge individual `suite/qubo/*.py` into `core/domain/` when validated
- Promote `suite/layers/` logic into `fusion_hero_os/core/` orchestrator
- Deprecate `legacy_sources/` after full cherry-pick review