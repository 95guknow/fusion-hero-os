# Quantenvektoren — fachmännische Monolith-Aufspaltung (Polyglot)

**Stand:** 2026-07-26 · **Platform:** Fusion Hero OS v13.0.0  
**Geltung:** **Spezifikation / Modell** (Zielarchitektur) — Umsetzung schrittweise unter BCG  
**Prinzip:** *Nicht eine Sprache für alles. Ein Quantum = ein Vektor (Zweck × Grenzfläche × SLA) × eine primäre Sprache.*  
**Zweifelsfall:** Jedes Quantum **darf** eine eigene Sprache wählen — **muss** aber einen **sprachneutralen Contract** exportieren.

---

## 1. Was ein „Quantenvektor“ hier ist

Kein Marketing-Quantum. **Arbeitsdefinition (Satz):**

> Ein **Quantenvektor** \(Q_i\) ist die kleinste **eigenständig deploybare** Einheit mit:
>
> 1. **einem klaren Zweck** (eine Verantwortlichkeit),  
> 2. **einer harten Grenze** (Process / Crate / Service / Worker),  
> 3. **einem Contract** (Schema + Geltung + Fehlercodes),  
> 4. **einer primären Sprache** (optimiert für den Zweck),  
> 5. **optionalen Fremdsprachen** nur hinter dem Contract.

**Nicht** ein Quantum: „noch ein Python-Import im fat Dashboard“.

**Vektor-Koordinaten** (zur Sortierung, nicht Metaphysik):

| Achse | Bedeutung |
|--------|-----------|
| **L** Latency-SLA | µs / ms / s / min |
| **I** Isolation | in-process / process / host / mesh |
| **M** Mutability | immutable / versioned / hot-reload |
| **S** Secrets surface | none / local / network |
| **G** Geltungsklasse | Satz / Bedingt / Modell / Fragment |

---

## 2. Zerlegungsregel (BCG + Force Highest Layer)

1. **Additive Evolution:** alte `import`-Pfade bleiben als **Facade** bis Quantum live.  
2. **Ein Quantum, ein Owner-Pfad** im Repo (`quanta/<id>/` oder bestehendes Crate).  
3. **Contract first:** OpenAPI / JSON-Schema / Cap’n Proto / flatbuffers — *bevor* Port.  
4. **Proof Registry:** jedes Quantum deklariert BEWIESEN/OFFEN/WIDERLEGT für Claims.  
5. **Im Zweifel eigene Sprache** — aber **ein** Wire-Format pro Boundary-Familie (siehe §5).

---

## 3. Quantenkarte (Ziel · 13 Vektoren)

Abgeleitet aus Ist: `fusion_hero_os.registry`, Layer-Registry, Dashboard fat-process, Rust crates, C-Bridge, PowerShell Ops, `ascension_os/`, GDrive cold, LLM frameworks.

| ID | Quantum (Vektor) | Zweck | Primärsprache | Sekundär / erlaubt | Isolation | Contract |
|----|------------------|--------|---------------|--------------------|-----------|----------|
| **Q0** | **MasterSeed / Integrity** | Fixpunkt, Hashes, push-layer-guard, Geltung | **Rust** | Python facade | process / lib | `integrity.v1` |
| **Q1** | **Control Plane** | Route, load-all, health, job dispatch | **Python 3** | — | process (Dashboard dünn) | HTTP/JSON OpenAPI |
| **Q2** | **Compute Hot Path** | QUBO, SA, parallel anneal, HT kernels | **Rust** | CUDA/C++ later | process / crate | `compute.v1` gRPC/IPC |
| **Q3** | **Agent Mesh** | MessageBus, TaskQueue, Supervisor, dual-agent | **Python 3** *oder* **Rust** wenn throughput | — | process | `agent.v1` |
| **Q4** | **Intelligence Fabric** | LLM frameworks, router, providers | **Python 3** | TS only for edge UIs | process | `llm.v1` |
| **Q5** | **Cold Storage / Spill** | GDrive offload, LongTermCache, medienserver | **PowerShell + Python tools** | bash on Linux | host jobs | `storage.v1` paths+manifest |
| **Q6** | **Mesh / Network** | Tailscale, connectors, mesh coord | **Python + Go\*** | Rust for proxies | multi-process | `mesh.v1` |
| **Q7** | **Surface UI** | Dashboard GUI, static, skins | **Python (FastAPI) + HTML/JS** | **TypeScript** when UI grows | process | HTTP static + WS |
| **Q8** | **Substrate Ops** | start_all, windows tune, exclusivity | **PowerShell** | Python helpers | host | env + exit codes |
| **Q9** | **Ascension Track** | CEC, Sisyphos, aspirational modules | **Python 3** | Julia later if math-heavy | loadable package / process | `ascension.v1` |
| **Q10** | **Kernel IPC Bridge** | C↔Python, AF_UNIX/TCP 19753 | **C + Rust** | Python client | process | `ipc.v1` binary+JSON |
| **Q11** | **Dissertation / Proof** | Text, proof_registry, kompendium | **Markdown + Python tooling** | Typst/LaTeX later | files | git + YAML proof |
| **Q12** | **Security / Persona / PII** | gates, scanners, consent | **Python 3** (+ policy YAML) | Rust for scanners if hot | lib/process | `security.v1` |

\*Go nur wenn Mesh-Ingress/Sidecar-Standard gewünscht; sonst Python behalten.

### Merksatz Sprache

| Domäne | Default |
|--------|---------|
| Glue, AI SDKs, Forschung, Agents | **Python 3** |
| CPU-hot, Parallel, Memory-safe kernel | **Rust** |
| ABI / OS-Bridge | **C** (dünn) + Rust |
| Windows Host-Automation | **PowerShell** |
| Produkt-UI wächst | **TypeScript** |
| Im Zweifel | **Sprache des Quantum-Owners** + **Contract Pflicht** |

---

## 4. Mapping Ist → Quantum (ohne Big-Bang)

| Heute (Monolith-Nähe) | Quantum | Sofort-Schnitt |
|----------------------|---------|----------------|
| `03_Code/Dashboard/app.py` fat startup | Q1 + Q7 | Preload bleibt, Compute auslagern |
| `fusion_hero_os/engine/*`, rayon crates | Q2 | `cargo` crate als Worker hinter IPC |
| `03_Code/llm_frameworks/*` | Q4 | eigener Prozess optional; erst Package-Boundary |
| `universal_startup_preload` | Q1 | orchestriert Contracts, importiert nicht alles in-process |
| `tools/disk_dedup_offload.py`, GDrive | Q5 | bleibt job-basiert |
| `kernel/bridge/*` | Q10 | IPC server first-class |
| `ascension_os/*` | Q9 | loadable; nie sole Kanon |
| `workstation/*.ps1`, `start_all.ps1` | Q8 | boot only |
| `push_layer_guard`, integrity | Q0 | vor jedem Push |
| `proof_registry.yaml`, docs/dissertation | Q11 | publication events |

---

## 5. Wire-Formate (sprachneutral)

Eine Familie pro Boundary — **nicht** pro Quantum ein neues Protokoll.

| Familie | Verwendung | Format |
|---------|------------|--------|
| **A** Control | health, load, jobs | HTTP/JSON · OpenAPI 3 |
| **B** Compute | anneal, quantize batch | gRPC *or* length-prefixed JSON over TCP (wie IPC 19753) |
| **C** Agent | tasks, heartbeats | JSON lines / NATS later |
| **D** Storage | manifests, offload index | JSON files + SHA-256 |
| **E** Events | bus, WS UI | JSON WebSocket |

**Regel:** Quantum in Sprache \(L\) implementiert **nur** den Contract; Clients sprechen Contract, nicht \(L\).

---

## 6. Repo-Layout (Ziel)

```text
quanta/
  Q0_integrity/          # Rust lib + thin CLI
  Q1_control_plane/      # Python package (dünnes FastAPI)
  Q2_compute/            # rust_engine_crate + pms_rust_kernel_crate (verschieben/align)
  Q3_agent_mesh/
  Q4_intelligence/
  Q5_cold_storage/
  Q6_mesh/
  Q7_surface/
  Q8_substrate_ops/      # ps1 + docs
  Q9_ascension/          # → ascension_os mirror
  Q10_ipc_bridge/        # kernel/bridge
  Q11_dissertation/
  Q12_security/
  CONTRACTS/             # openapi/, schemas/, proto/
  facades/python/        # BCG: alte import-Pfade → Client-Stubs
```

Bis zur Migration bleiben **bestehende Pfade** Facades.

---

## 7. Phasenplan (fachmännisch, BCG)

### Phase A — **Schnitt zeichnen** (1–2 Sessions)
- [x] Diese Spezifikation  
- [ ] `quanta/CONTRACTS/` Skeleton + `quantenvektoren.yaml` (Maschinenkarte)  
- [ ] Jedes DEFAULT_MODULES-Entry in Registry → Quantum-ID taggen  

### Phase B — **Q2 + Q10 first** (höchster Nutzen)
- Compute-Hot-Path und IPC als **eigene Prozesse**  
- Dashboard ruft nur Contract (kein in-process anneal default)  
- Sprache: Rust + C wie geplant  

### Phase C — **Q4 / Q3 package boundary**
- LLM frameworks + agents: eigene Packages, optional eigener Process  
- Python bleibt primär  

### Phase D — **Q1 dünn**
- `app.py` nur Surface + Control; Preload = Contract fan-out  
- Frameworks „always on“ = **Q4 process up**, nicht „alles in einem Interpreter“  

### Phase E — **Q5/Q8 härten**
- GDrive spill + start_all als Ops-Quanta mit Manifests  

### Phase F — **Q9/Q11/Q0/Q12**
- Ascension loadable; Proof/Security/MasterSeed als harte Gates  

---

## 8. Entscheidungsmatrix „eigene Sprache im Zweifel“

```text
IF latency < 5ms AND CPU-bound     → Rust (Q2/Q0)
IF AI SDK / glue / research        → Python (Q1/Q3/Q4/Q9)
IF Windows host automation         → PowerShell (Q8)
IF stable ABI to OS                → C thin + Rust (Q10)
IF browser product UI              → TypeScript (Q7 growth)
IF pure documents / proof          → Markdown+YAML (Q11)
ELSE                               → Owner wählt Sprache;
                                     MUST ship CONTRACT + test harness
```

**Verbot:** neue Sprache ohne Contract, CI-Job und Facade.

---

## 9. Anti-Patterns (explizit)

| Anti-Pattern | Ersatz |
|--------------|--------|
| Rewrite everything in Rust | Nur Q2/Q0/Q10 hot |
| Microservice pro Datei | Quantum = SLA-Einheit |
| Shared mutable Python globals across quanta | Contract + versioned messages |
| „Polyglot“ ohne Schema | polyglot chaos |
| Ascension als operativer Kanon | Q9 bleibt aspirational |

---

## 10. Erfolgskriterien

1. `start_all` startet **Q8→Q1/Q7**; Q4 frameworks ready **ohne** fat import-all-fail.  
2. Q2-Bench: gemessener Speedup vs. reines Python-SA.  
3. Jedes Quantum hat `CONTRACTS/<id>.v1.yaml` + Health.  
4. BCG: `from fusion_hero_os...` Facades grün für ≥1 Minor.  
5. Proof Registry listet Quantum-Claims.

---

## 11. Bezug

- Registry Ist: `fusion_hero_os/registry.py`  
- Layer Ist: `fusion_hero_os/core/layer_registry.py`, `fusion_unified.yaml`  
- Polyglot Ist: Rust crates, `kernel/bridge`, `workstation/*.ps1`  
- Spill: `docs/ops/GDRIVE_SPEICHERAUSLAGERUNG.md`  
- Maschinenkarte: `docs/architecture/quantenvektoren.yaml`

**Schluss-Satz:** Der Monolith wird nicht „ersetzt“, sondern **entlang von Quantenvektoren factorisiert**; Sprachen sind **Koordinaten der Optimierung**, nicht Identitäten des Systems. Das System bleibt **Dissertation-as-OS** — die Quanta sind seine Kapitel mit ABI.
