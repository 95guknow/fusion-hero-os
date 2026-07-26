# Dual + Virtual Timeline Auto-Training — t ∥ τ ∥ v

**Platform:** Fusion Hero OS **v12.0.0**  
**Cycle:** BIG ALPHA  
**Policy:** pseudo_inhouse_only · freemium=false · labor sandbox only  
**Config:** `training_dual_timeline.yaml`  
**Code:** `fusion_hero_os/core/dual_timeline_training.py`

## Principle

Auto-training scans available knowledge files and places samples on **parallel timelines**:

| Axis | Symbol | Meaning | Geltung |
|------|--------|---------|---------|
| **Real time** | \(t\) | File mtime (UTC chronology) | Satz (filesystem) |
| **Imaginary time** | \(\tau \in [0,1]\) | Structural depth + Geltung + **heroic weight** | Modell |
| **Virtual** | \(v\) | Heroic labor scenarios for operator (**SHU/dich**) | Modell / Bedingt |

### Virtual timelines — re-enabled (BIG ALPHA)

Virtual timelines are **allowed again** under lab bounds:

- Labor / pure Erkenntnisgewinn only  
- `INVERT(realraum) = labor_hypothesis + integrity_probe + no_vault_commit`  
- Offense **FORBIDDEN**  
- Heroically optimized for the operator (SHU = dich / St3phaN): MasterSeed, Eudaimonia, Sisyphos, PeerReview, honest Geltung  

```
files ──scan──► events(t, τ, H)
                    │
                    ▼
              dual samples (heroic prompt)
              virtual samples (if H ≥ threshold)
              timeline_dual.json  (real ∥ imaginary ∥ heroic_ranked)
              consistency_report.json
```

## Run

```powershell
python scripts/auto_train_dual_timeline.py
# or
python -m fusion_hero_os.core.dual_timeline_training
python -m fusion_hero_os.core.dual_timeline_training --status
```

API (Dashboard :8000):

- `GET /api/training/dual-timeline/status`
- `POST /api/training/dual-timeline/run`
- `GET /api/training/dual-timeline/catalog`

## Config gates

```yaml
virtual_timelines:
  enabled: true
  min_heroic_score_for_virtual: 0.12
  max_virtual_samples_per_file: 4

heroic_optimization:
  enabled: true
  target: operator_shu
```

## Outputs

| Path | Content |
|------|---------|
| `~/.fusion/training/dual_timeline/samples_dual_timeline.jsonl` | dual + virtual samples |
| `~/.fusion/training/dual_timeline/timeline_dual.json` | dual indices + heroic ranked |
| `~/.fusion/training/dual_timeline/consistency_report.json` | consistency heuristics |
| `docs/training/dual_timeline_training.latest.json` | repo-visible summary |

## Honesty

- \(\tau\) and \(v\) mappings are **Modell** (not physics proofs).  
- Virtual ≠ Realraum. No private vault in git.  
- Parallelism is operational: multiple sort orders, one corpus, consistency checks.  
- BCG: dual-only path remains valid if `virtual_timelines.enabled: false`.
