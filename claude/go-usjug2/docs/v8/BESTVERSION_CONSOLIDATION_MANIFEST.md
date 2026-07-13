# Bestversion Consolidation Manifest

**Generated:** 2026-07-06T06:25:09.553434+00:00
**Canonical target:** `fusion-hero-os` (v8 best version)

## Strategy

Per `docs/V8_STRATEGY.md`, `fusion-hero-os` is the single active development repo.
All other `95guknow` repositories are legacy/idea sources. Unique files are copied
into `legacy_sources/<repo>/` for bottom-up cherry-picking.

## Source Repositories

| Repository | Total Files | Unique | Imported |
|------------|-------------|--------|----------|
| `private-hacking-suite` | 138 | 119 | 119 |
| `FuHOS_pub` | 225 | 43 | 43 |
| `kilo` | 13 | 13 | 13 |
| `Fusion_Hero_OS_v1.1` | 15 | 7 | 7 |
| `heroic-fusion-os-manifest` | 8 | 7 | 7 |
| `dashboard` | 10 | 7 | 7 |
| `fusion-hero-os-v1` | 5 | 4 | 4 |
| `mister-Contributor-gui` | 5 | 3 | 3 |
| `alte-frau-95g-heroic-core` | 3 | 2 | 2 |
| `heroic-core-foundation` | 9 | 2 | 2 |
| `fusion-hero-core` | 6 | 0 | 0 |
| `fusion-hero-os-daily-plans` | 1 | 0 | 0 |

## Next cherry-pick priorities

1. `heroic-fusion-os-manifest` — README / narrative style
2. `dashboard` — Flask UI templates
3. `private-hacking-suite` — QUBO/GPU/fusion tooling
4. `heroic-core-foundation` — foundation checks
5. Smaller seeds (`fusion-hero-os-v1`, `alte-frau-95g-heroic-core`, daily-plans)

Full machine inventory: `docs/v8/bestversion_inventory.json`
