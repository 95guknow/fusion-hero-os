# Fusion Hero OS

[![Release](https://img.shields.io/badge/Release-v10.0.0-00C853?style=for-the-badge&logo=github)](https://github.com/95guknow/fusion-hero-os/releases/tag/v10.0.0)
[![Platform](https://img.shields.io/badge/Platform-10.0.0-blue?style=for-the-badge)](VERSION)
[![Governance](https://img.shields.io/badge/Governance-Stage_A%2FB-1E88E5?style=for-the-badge)](#stage-ab-governance)

**Hybrid AI / mainframe platform** | operative kanon **v10.0.0**  
Core: **ALTE_Frau_95g Heroic Core** | additive over the v8.3 stack (BCG)

### Dissertation-as-OS (canonical ontology)

> **The entire Fusion Hero OS *is* the dissertation.**  
> The monograph / PDF / abstract is **only one form of expression**.

**Design template V3.3 is mandatory** (work quality must not regress):  
[docs/kompendium/V3.3_DESIGNVORLAGE_VERBINDLICH.md](docs/kompendium/V3.3_DESIGNVORLAGE_VERBINDLICH.md) ·  
Original PDF: `legacy_sources/heroic-fusion-os-manifest/Kompendium_der_Heroik_V3.3.pdf`  
→ Mythos · Grund · Beweis · claim marks Satz/Bedingt/Modell/Fragment · Synthese + 6 Bögen · no metaphor-as-proof.

| Expression | Examples |
|------------|----------|
| Operative | this repo, runtime, dashboard, mesh, MCP |
| Textual | [docs/dissertation/](docs/dissertation/) PDF · DOCX · abstracts |
| Empirical | live hot-runs, health, releases, coordinator |
| Epistemic | Proof Registry (PROVEN / OPEN / REFUTED) |
| Archival | Master Archive, kompendia V3.3→v10, curriculum |

Ontology: [docs/dissertation/ONTOLOGIE_DISSERTATION_IST_DAS_OS.md](docs/dissertation/ONTOLOGIE_DISSERTATION_IST_DAS_OS.md) ·  
Index: [docs/DISSERTATION_AS_OS.md](docs/DISSERTATION_AS_OS.md) ·  
Bifocal verweis (universe ↔ brain · Standard Model, **Model/OPEN**): [docs/dissertation/VERWEIS_BIFOKALITAET_UNIVERSUM_GEHIRN_SM.md](docs/dissertation/VERWEIS_BIFOKALITAET_UNIVERSUM_GEHIRN_SM.md) ·  
Release: [dissertation-v1.0](https://github.com/95guknow/fusion-hero-os/releases/tag/dissertation-v1.0)

> This public repository must not contain personal profile data, private
> locations, or live Tailscale inventory (IPs, node IDs, private MagicDNS).
> Runtime topology lives only on the operator machine / private config.

---

## Architecture

```
[ Dashboard :8000  GUI + REST + WS ]
              |
              v
[ Mainframe core: fusion_hero_os / ALTE_Frau_95g ]
  QUBO | multi-agent | layer registry | AutoLoad | mesh registry
              |
              v
[ Tailscale mesh + MCP connector segments ]
  (roles/config in repo = placeholders; live values stay local)
```

| Layer | Content | Status |
|-------|---------|--------|
| Platform v10.0.0 | Unified versioning, Stage-A/B gates | operative |
| Heroic stack (ex-v8.3) | QUBO, agents, layers, mesh, dashboard | operative |
| AscensionOS v9.x | `ascension_os/` CEC, AscensionCore, Sisyphos | loadable / roadmap |

```typescript
const fusionHeroOS = {
  version: "10.0.0",
  tag: "v10.0.0",
  system_state: "Operational + Governed",
  compatibility: "Backward-compatible with v8.3 baseline (BCG)",
  active_core: "ALTE_Frau_95g Heroic Core",
  layers: [
    "Stage-A: privacy, consent gate, archive scrypt KDF, version unity",
    "Stage-B: depersonalization + persona/PII regression scanners",
    "Operative stack: QUBO, multi-agent, 13-layer registry, mesh, dashboard",
    "AscensionOS v9.x: loadable roadmap (not sole kanon claim)",
  ],
};
```

See [BEST_VERSION.md](BEST_VERSION.md) for honest operative vs roadmap status.

---

## Quick Start

```powershell
# Full boot (AutoLoad can take minutes)
powershell -File start_all.ps1

# Fast-Boot (recommended)
cd 03_Code\Dashboard
$env:FUSION_AUTO_LOAD = "0"
$env:FUSION_HYPERTHREADING = "1"
python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

### Docker (Senfkorn production / GCE europe-west3)

```bash
docker compose up --build -d
# or: bash workstation/gce_docker_deploy_senfkorn.sh
```

| Endpoint | Purpose |
|----------|---------|
| http://127.0.0.1:8000 | Standard GUI |
| `/mainframe` | Mainframe hub (dissertation surface) |
| `/mainframe/grok` | Grok interconnect control plane |
| `/api/grok/routes` | Canonical route table |
| `/api/ai/inhouse/status` | Pseudo-inhouse AI hub (freemium=false) |
| `/api/creative/inhouse/status` | Pseudo-inhouse creative (image/video/PDF) |
| `/v1/chat/completions` | OpenAI-compatible local AI facade |
| `/v1/images/generations` | OpenAI-compatible local image facade |
| `/api/health?light=true` | Fast health probe |
| `/api/health` | Full status |
| `/docs` | OpenAPI |

Full guide: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

### Version / health gates

```powershell
python scripts/bump_version.py --check
python scripts/repo_health_check.py
```

---

## Tailscale Mesh

**Principle:** each connector is its own mesh segment (ID, host, health, tag).  
Public configs use **placeholders only** (`*.example.ts.net`). Do not commit live inventory.

| File | Role |
|------|------|
| `mesh_connectors.yaml` | Segment registry (placeholders) |
| `src/normal_os/integration/mesh_roles.yaml` | Role assignments |
| `mesh_virtual_exit_nodes.yaml` | Exit profiles (placeholders) |
| [docs/mesh/README.md](docs/mesh/README.md) | Ops notes |

---

## Stage-A/B Governance

| Stage | Shipped |
|-------|---------|
| **A** | PII cleanup, consent gate, archive scrypt KDF, version consistency |
| **B** | Package depersonalization, persona/PII regression scanners |

Public surface policy: no personal identity, no private location, no live mesh inventory in this repo.

---

## Tech Stack

| Domain | Stack |
|--------|--------|
| Runtime | Python 3.11+ / FastAPI / Uvicorn / Numba |
| Performance | Rust crates (`pms_rust_kernel_crate`, `rust_engine_crate`) |
| Mesh | Tailscale / per-connector registry |
| AI | Local model hooks / Integration Hub |
| Deploy | Docker Compose / GCE europe-west3 |
| CI | pytest + proof-registry + PII gate + version gate |

---

## Documentation

| Doc | Role |
|-----|------|
| [BEST_VERSION.md](BEST_VERSION.md) | Operative kanon vs roadmap |
| [docs/dissertation/](docs/dissertation/) | **Dissertation-as-OS** · abstracts · ontology · bifocal verweis |
| [docs/mesh/GROK_INTERCONNECT.md](docs/mesh/GROK_INTERCONNECT.md) | Interconnect graph + re-routes |
| [docs/mesh/PSEUDO_INHOUSE_AI.md](docs/mesh/PSEUDO_INHOUSE_AI.md) | Pseudo-inhouse LLM facade (no freemium) |
| [docs/mesh/PSEUDO_INHOUSE_CREATIVE.md](docs/mesh/PSEUDO_INHOUSE_CREATIVE.md) | Image/Video/PDF/Graphics pseudo-inhouse |
| [docs/mesh/PUSH_LAYER_GUARD.md](docs/mesh/PUSH_LAYER_GUARD.md) | Layer-woven push guard (wanted vs unwanted) |
| [docs/ops/DEPLOY_PUSH_MERGE.md](docs/ops/DEPLOY_PUSH_MERGE.md) | **deploy=private · push=public · merge=both(timeline)** |
| [docs/mesh/MAINFRAME_WEBSITE.md](docs/mesh/MAINFRAME_WEBSITE.md) | Dauer-VR · IDE · Worktree |
| [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) | Boot / ports / troubleshooting |
| [BRANCH_STRATEGY.md](BRANCH_STRATEGY.md) | SemVer / tags |
| [docs/mesh/README.md](docs/mesh/README.md) | Mesh ops (placeholders) |
| [docs/business/senfkorn_businessplan.yaml](docs/business/senfkorn_businessplan.yaml) | Senfkorn energy/pricing anchors |
| [ascension_os/](ascension_os/) | Ascension track (loadable) |

---

## Modules

- **fusion_hero_os/** - core package `10.0.0` (Active)
- **03_Code/Dashboard/** - mainframe GUI + API (Active)
- **Mesh tooling** - public placeholders; live data local only
- **Energy pricing daemon** - `scripts/run_energy_pricing_daemon.py` / Docker service
- **CI gates** - Stage-A/B pytest + `scripts/repo_health_check.py` (Enforced)

---n

**Release:** [v10.0.0](https://github.com/95guknow/fusion-hero-os/releases/tag/v10.0.0)