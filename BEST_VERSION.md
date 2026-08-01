# BEST VERSION — Fusion Hero OS

**Stand:** v15.0.0 canonical (VERSION, ungetaggt) — additive over v14.0.0 / v13.0.0 / v12.1.0 / v12.0.0 / v10 / v8.3 BCG  
**v15.0.0:** Platform major (Ära 15) — **ohne benannten Ära-Inhalt.** Der Sprung ist bisher ein reiner Versionssprung: Manifeste, Doku, Satelliten-Kompatibilität. Ein Ära-Name wird erst eingetragen, wenn es etwas zu benennen gibt.  
**v14.0.0:** Platform major (Ära 14) — **Poly-Mesh / n-dimensionale Mannigfaltigkeit**; Claude Science Integration (Multi-Agent Audit, Scientific Connector Protocol, ScientificAuditHorkrux). Der Ära-Kern ist **ASPIRATIONAL/OFFEN**, siehe `proof_registry.yaml` — die Nummer ist gesetzt, nicht belegt.  
**v13.0.0:** Platform major (Ära 13) — daycycle + A13/psychogramm/coworking CI; dual-org merge; AscensionOS v9.10 aspirational  
**Best-of-today (post-tag, same major):** Live GraphAPI landing dual viz · ASM kernel inject · public UI-stub · GDrive spill · quantenvektoren polyglot map · non-blocking dashboard boot  
**v12.1.0:** Daycycle mem (minute→private dev hourly→4h PR→daily top+fanout) · agent protocol wake `testtest`

Dieses Dokument benennt den besten, kohärenten Stand des Systems — und
trennt explizit den **operativen Kanon** von Roadmap-/Forschungs-Tracks
(siehe `docs/v8/erkenntnisse_index.yaml` → `bestversion-vs-ascension`,
erweitert um v10 Stage-A/B).

## Dissertation-as-OS

> **Das gesamte Fusion Hero OS ist die Dissertation.**  
> Der Text (Monographie/PDF/Abstract) ist nur **eine** Form seines Ausdrucks.

### Designvorlage V3.3 — zwingend (Arbeitsqualität)

Original und Verfassung der Textqualität:

| Asset | Pfad |
|-------|------|
| **Original PDF** | `legacy_sources/heroic-fusion-os-manifest/Kompendium_der_Heroik_V3.3.pdf` |
| **Verbindliche Vorlage** | `docs/kompendium/V3.3_DESIGNVORLAGE_VERBINDLICH.md` |
| Extrakt | `docs/kompendium/_extract_v33.txt` |

**Nicht opfern:** Synthese + 6 Bögen + Anhang · Geltung Satz/Bedingt/Modell/Fragment · Register Spezifikation / Heroischer Exkurs / Herleitung aus dem Nichts · Duktus Mythos·Grund·Beweis · keine Metapher-als-Beweis. v10 und Dissertation-as-OS sind **additiv** zu V3.3, nicht Ersatz.

| Ausdruck | Ort |
|----------|-----|
| Operativ | dieses Repo + Dashboard :8000 + Mesh + MCP |
| Textuell | `docs/dissertation/` · Release `dissertation-v1.0` |
| Ontologie | `docs/dissertation/ONTOLOGIE_DISSERTATION_IST_DAS_OS.md` |
| Bifokal-Verweis | `docs/dissertation/VERWEIS_BIFOKALITAET_UNIVERSUM_GEHIRN_SM.md` (Universum↔Gehirn · Standardmodell; Modell/OFFEN) |
| Control Plane | `/mainframe/grok` · `/api/grok/route` · `/api/grok/routes` |

Code Honesty bleibt organisch: Proof Registry **BEWIESEN / OFFEN / WIDERLEGT** — die Ontologie entbindet nicht von Nachweis.

## Operativer Kanon: v15.0.0 / main

**`VERSION` = `15.0.0` ist die kanonische Plattform-Version** (additiv zu v14.0.0 / v13.0.0 / v12.1.0 / v12.0.0 / v10 / v8.3). Quelle der
Wahrheit: annotierter Git-Tag `v15.0.0` auf `main` (nach Release) + Root-`VERSION`.
Alle Manifeste (`pyproject.toml`, `package.json`, Crate-`Cargo.toml`,
`fusion_hero_os.__version__`) müssen übereinstimmen (`scripts/bump_version.py --check`).

> **Stand des Tags — zwei Ären ohne Release.** `VERSION` steht auf 15.0.0, das
> letzte **veröffentlichte** Release ist `v13.0.0`. Weder v14.0.0 noch v15.0.0
> sind getaggt. Damit stimmt die Regel „Quelle der Wahrheit ist der annotierte
> Tag" (`BRANCH_STRATEGY.md`) für zwei aufeinanderfolgende Majors nicht mehr —
> die `VERSION`-Datei ist der Kanon vorgelaufen.
>
> Das ist keine Feinheit: die Landing Page nennt v14.0.0 und verlinkt auf
> `/releases/latest`, was weiterhin v13.0.0 ausliefert. Nachziehen mit
> `git tag -a v14.0.0 <commit-cfbb751>` und `git tag -a v15.0.0` auf `main`;
> `.github/workflows/release.yml` feuert auf `v[0-9]+.[0-9]+.[0-9]+` und baut
> das Release dann selbst.

### Was v15.0.0 operativ bedeutet (ehrlich)

Ära 15 ist **additiv** über v14 und trägt **keinen benannten Inhalt**. Der
Sprung umfasst bislang genau das:

| Schicht | Inhalt | Status |
|---------|--------|--------|
| **Plattform v15.0.0** | Manifeste synchron, Satelliten-Kompatibilität nachgezogen | **operativ** |
| **v14-Stack** | Poly-Mesh-Ära, Claude Science Integration | **erhalten** (Status unverändert, siehe unten) |
| **Ära-15-Inhalt** | — | **nicht benannt** |

Es gibt hier bewusst keinen Ära-Titel. v14 heißt „Poly-Mesh / n-dimensionale
Mannigfaltigkeit" und trägt drei `OFFEN`-Claims, die bis heute unbelegt sind;
ein zweiter Name über einem zweiten unbelegten Kern würde die Lücke zwischen
Nummer und Beweis nur verdoppeln. Sobald es einen Befund gibt, der eine Ära
trägt, kommt der Name hierher — nicht vorher.

Die Ära-14-Claims bleiben davon unberührt: sie sind weder erledigt noch
verfallen, sie stehen unverändert `OFFEN` in `proof_registry.yaml`.

### Was v14.0.0 operativ bedeutet (ehrlich)

Ära 14 ist **additiv** über dem v13-Stand, der seinerseits additiv über dem
v8.3-Funktionskern liegt (BCG ununterbrochen). Was die Ära benennt und was sie
bereits leistet, ist ausdrücklich **nicht dasselbe**:

| Schicht | Inhalt | Status |
|---------|--------|--------|
| **Plattform v14.0.0** | Einheitliche Manifest-Version, Gate deckt `__version__` mit ab | **operativ** |
| **v13-Stack (ex-v13.0.0)** | Daycycle, A13, Discharge-Runden, Consent-Gate, Hypercluster | **operativ** (erhalten) |
| **Poly-Mesh / n-d Mannigfaltigkeit** | Ära-Titel; Zitterpolymesh, fraktales Mainframe-Mesh, Mannigfaltigkeits-Lesart | **ASPIRATIONAL / OFFEN** |
| **Claude Science Integration** | MultiAgentResearchLane, ScientificAuditHorkrux, Connector-Protokoll | **ASPIRATIONAL / STUB** |
| **AscensionOS v9.x** | CEC, AscensionCore, Sisyphos, … in `ascension_os/` | **loadable / Roadmap** |

Der Ära-Name ist eine **Richtungsangabe, kein Befund**. Die zugehörigen Claims
stehen in `proof_registry.yaml` mit Status `OFFEN` und ohne `proofs:` — genau
so lange, bis sammelbare pytest-Knoten sie tragen. Eine Major-Nummer entlastet
nicht vom Nachweis; das ist dieselbe Regel, unter der v9 nie ein alleiniges
Platform-Release bekommen hat.

### Was v10.0.0 operativ bedeutet (ehrlich)

v10 ist **additive Evolution** über den v8.3-Stack (BCG — Backward Compatibility
Guarantee). Es ersetzt den v8-Funktionskern nicht; es härtet und vereinheitlicht ihn.

| Schicht | Inhalt | Status |
|---------|--------|--------|
| **Plattform v10.0.0** | Einheitliche Versionierung, Stage-A/B Gates | **operativ** |
| **Heroic Stack (ex-v8.3)** | QUBO, Multi-Agent, Layer-Registry, Mesh, Dashboard | **operativ** (erhalten) |
| **AscensionOS v9.x** | CEC, AscensionCore, Sisyphos, … in `ascension_os/` | **loadable / Roadmap** (nicht „alles ist v9“) |

### v10 Stage-A (stabilisiert in #66)

- Plattform-Version **10.0.0** in allen Manifesten
- PII-Cleanup im aktiven Tree
- Ascension **consent gate** (fail-closed für personenbezogene Ops)
- Archive-Anker: scrypt-KDF, neutrales Salt `fusion-hero-os|archiv|v10` (archiv_version 2.0)
- Asset-/Pfad-Stabilisierung nach Scrub

### v10 Stage-B (stabilisiert in #67)

- Depersonalisierung im aktiven `fusion_hero_os`-Paket
- Persona-Token-Regressionsscanner (CI-Gate)

### Operator-Person-Extraktion (2026-07-16)

- Rolle **`operator`** ist abstrakt; Legal/academic Person (**Urban**) aus dem Runtime-Kernel **herausgelöst**
- Membrane: `fusion_hero_os.core.operator_identity` · Vault: `~/.fusion/operator/identity.local.json`
- Scan/Report: `python scripts/extract_operator_urban.py` · Doc: `docs/security/OPERATOR_IDENTITY_MEMBRANE.md`
- Dissertation/Academia behalten Autorennamen (Publication-Surface); operatives Paket person-clean

### API-Plane-Trennung Hyperraum / Business (2026-07-16)

- **hyperraum** = halbprivater Operator-Hyperraum · **business** = klassische Product-API
- Katalog `api_planes.yaml` · Classifier `fusion_hero_os.core.api_plane` · Routes `/api/planes`, `/api/v1/business/*`, `/api/hyperraum/*`
- Doc: `docs/architecture/API_PLANE_SEPARATION.md` · Legacy-Pfade bleiben (additive BCG)

### OS → Poly-Mesh Port (2026-07-16)

- OS-Organe auf L0–L3 gemappt (`mesh_os_port.yaml`)
- Runtime `fusion_hero_os.core.poly_mesh_os_port` · CLI `python scripts/port_os_poly_mesh.py`
- Registry: `~/.fusion/mesh/os_port/latest.json` · Doc: `docs/mesh/OS_POLY_MESH_PORT.md`
- Secrets bleiben L1; AudioRelay mesh-only; Tailscale Apps-UI ≠ OS-Port

### Kostenfunktion v2.0 (2026-07-16)

- \(C_h=C_{L1}+C_{L2}+C_{L3}+C_{L4}\) · FEU · kompetitive \(P_{1k}\) · soft \(\Pi(\mathrm{tier})\)
- Modul `fusion_hero_os.core.poly_mesh_cost_function` · Businessplan **v1.2**
- API: `GET /api/v1/business/cost-function` · Doc: `docs/business/COST_FUNCTION_v2.md`

### Ererbter v8.3-Funktionskern (weiterhin operativ)

- QUBO-Engine (`fusion_hero_os/engine/mainframe.py`, Numba + optionales Rust-Backend)
- Multi-Agenten-Orchestrierung (`fusion_hero_os/orchestration/agents.py`)
- Layer 0/4/5 Orchestrator (`fusion_hero_os/core/heroic_core_orchestrator.py`)
- Tailscale-Mesh + MCP-Konnektoren (`tailscale_mesh_registry.py`, `mesh_connectors.yaml`)
- LLM-Frameworks + Integration Hub (`fusion_integration_hub.py`, `llm_frameworks.yaml`)
- Layer-Registry über alle 13 Layer (`fusion_hero_os/core/layer_registry.py`)
- Dashboard Standard-GUI `http://127.0.0.1:8000` (`03_Code/Dashboard/app.py`)
- CI-Gates: pytest (inkl. v10 Stage-A/B) + Proof-Registry + Erkenntnis-Index + Version-Consistency

## Roadmap-/Forschungs-Track: AscensionOS v9.x

`ascension_os/` enthält den visionären v9.x-Track. Er ist **kein** separates
MAJOR-Release und **nicht** der alleinige operative Kanon. Seit v8.3 als
optionaler Layer (`ascension`) in `fusion_unified.yaml` registriert und über
`QuadCoreBridge(mode="ascension")` nutzbar; v10 ergänzt Consent-Gating.

1. **CoEvolutionaryClosure (CEC) v9.3** — MasterSeed Strict Contraction, HT-Tracks  
2. **AscensionCore v9.4** — Sisyphos, Psycholysis, LLM Core, MasterSeed  
3. **PersistentSisyphosCycle v9.4** — Historie + JSON-Persistence  
4. **GenerationalEvolutionEngine** — Inside-Out, coevolutionär  

## Architektur-Prinzipien

- **Dissertation-as-OS**: Betrieb *ist* die Arbeit; Text ist Verdichtung, nicht das Ganze.
- **V3.3 Designvorlage**: Kompendium-Qualität ist Pflicht; Changelog-Duktus ersetzt keinen Satz.
- **Inside-Out**: MasterSeed / Sisyphos im Kern, Strahlung nach außen.
- **Coevolutionär**: kontrollierte gegenseitige Beeinflussung.
- **Pure Core (Langzeit)**: Operator = reiner Core; Stärken = formale Mathematik + diverse Algorithmen; Rest = fremde Stärken (mutual, peripheral). Membrane: `fusion_hero_os/core/pure_core_coevolution.py` · Katalog `core/catalogs/pure_core_strengths.yaml` · Doc `docs/architecture/PURE_CORE_COEVOLUTION.md`. Core nie durch SaaS/LLM ersetzt.
- **Bifokal**: Kosmos-Pfad (u. a. SM-Referenz) und Gehirn-/Operativ-Pfad als Dualität, nicht Identität.
- **Persistent + Stateful**: kritische Zustände werden persistiert.
- **BCG / Additive Evolution**: neue Versionen entfernen keine alten Fähigkeiten.
- **Ehrlich**: Roadmap-Anspruch ≠ Ist-Zustand (`proof_registry.yaml`, Status-Reports).

## Deploy (v10.0.0)

```powershell
# Gates
python scripts/bump_version.py --check
python -m pytest tests/test_version_consistency.py tests/test_archive_salt.py `
  tests/test_ascension_consent.py tests/test_asset_persona_paths.py `
  tests/test_persona_scanner.py tests/test_pii_scanner.py -q

# Lokal
powershell -File start_all.ps1
# oder Fast-Boot: $env:FUSION_AUTO_LOAD=0; uvicorn in 03_Code/Dashboard

# Alles auf v10 aktivieren (Registry + Dashboard load-all/autoload/interconnect)
python scripts/activate_v10.py
# Dissertation-Anhänge-Pipeline (aktiviert v10 automatisch)
python scripts/pipeline_dissertation_v10.py

# Release
git tag -a v10.0.0 -m "Fusion Hero OS v10.0.0 — operational platform"
git push origin main --tags
gh release create v10.0.0 --generate-notes --title "Fusion Hero OS v10.0.0"
```

Siehe `DEPLOYMENT_GUIDE.md`, `BRANCH_STRATEGY.md`.

## Nächste logische Erweiterungen (Roadmap)

- HorkruxSelfUpdateProtocol (governance-fähig)
- Volle Cross-Track-Synergie Heroic ↔ Ascension
- Systemweiter EudaimoniaGuard
- Durable encrypted vault transport (Threat Model Stage-1 out-of-scope)
