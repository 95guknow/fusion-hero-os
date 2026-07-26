# Tailscale Quantize Self-Mod

**Platform:** Fusion Hero OS v12.0.0 · BIG ALPHA  
**Config:** `mesh_quantize_selfmod.yaml`  
**Code:** `fusion_hero_os/core/tailscale_quantize_selfmod.py`  
**Policy:** sandbox_only · offense FORBIDDEN · no foreign ACL mutation

## Zweck

Selbstständig erzeugte **Tailscale-Assist-Rollen**, die die **Quantisierung von Berechnungen** (QUBO / bit-depth / Annealing) **selbstmodulierend** unterstützen:

| Assist | Tag | Funktion |
|--------|-----|----------|
| quantize-annealer | `tag:fuse-quantize-anneal` | parallele SA-Shards |
| quantize-bitreducer | `tag:fuse-quantize-bits` | adaptive Bit-Tiefe |
| quantize-integrity | `tag:fuse-quantize-integrity` | Integritäts-Probe |
| quantize-partition | `tag:fuse-quantize-partition` | Partition / Fan-out |
| quantize-eudaemon | `tag:fuse-quantize-eudaemon` | Param-Drift → Fixpunkt |

## Selbstmodulation

Mesh-Signal (read-only Tailscale status):

\[
\text{scale} = \mathrm{clamp}\bigl(\frac{\text{peers\_online}}{\text{peer\_target}}, 0.15, 1\bigr)
\]

Offline / virtual floor → konservative lokale Kapazität (MasterSeed-Kontraktion).

Mappt scale → `bit_depth`, `anneal_steps`, `workers`, `partitions`, `T0`.

## Ehrlichkeit

- **Keine** automatische Tailnet-ACL-Schreibung an fremde Orgs.
- **Keine** Remote-Code-Execution auf Peers (Worker = lokaler Fan-out, gelabelt).
- Virtual nodes sind **explizit** `virtual: true`.
- Peers counts = **Satz**; Parameter-Map = **Modell**.

## CLI

```powershell
python -m fusion_hero_os.core.tailscale_quantize_selfmod --status
python -m fusion_hero_os.core.tailscale_quantize_selfmod --cycle
python -m fusion_hero_os.core.tailscale_quantize_selfmod --cycle --heroic 0.3
```

## API

| Method | Path |
|--------|------|
| GET | `/api/mesh/ops/quantize-selfmod` |
| POST | `/api/mesh/ops/quantize-selfmod/ensure` |
| POST | `/api/mesh/ops/quantize-selfmod/modulate?heroic=0.2` |
| POST | `/api/mesh/ops/quantize-selfmod/cycle?heroic=0.2` |

## State

- `~/.fusion/mesh/quantize_selfmod/nodes.json`
- `~/.fusion/mesh/quantize_selfmod/last_selfmod.json`
- `~/.fusion/mesh/quantize_selfmod/last_quantize_run.json`
- `docs/mesh/tailscale_quantize_selfmod.latest.json`
