# Ideen-Backlog — nicht implementierte Ideen aus allen Archiven

**Erstellt:** 2026-07-04 (Archiv-Sweep + GitHub-Abgleich via `gh`)
**Quellen:** `docs/99_archive/`, `06_Master_Archive/` (PDFs), `archive/`, `v2_beta/`,
`04_Buch_und_Archiv/`, `docs/04_execution/PMS_OPERATOR_CATALOG_v7.5.md`,
GitHub-Konto `95guknow` (11 Repos, Stand 2026-07-04), lokale `.grok/`-Spuren.

**Regel:** Jede Idee trägt einen ehrlichen Status. Kein Eintrag wird als "umgesetzt"
markiert ohne nachprüfbaren Beleg (Datei, Repo, Commit).

---

## A. Nicht umgesetzt (reines Konzept)

### A1. Timespace-Upgrade + geometrisches Token-Management
- **Quelle:** `v2_beta/Timespace_Upgrade_Proposal_v2_beta.md` + `v2_beta/TokenManagementSystem.py`
- **Befund:** Scaffold `03_Code/timespace_token_management.py` (geometrische Priorität + TMS-Brücke, 2026-07-05). Volle Zeitaum-Vision aus Grok-Projekten nicht exportiert.
- **Status:** TEILWEISE — Minimal-Scaffold implementiert; volle Grok-Version offen.

### A2. HeroicLLM-EA Orchestrator (LLM + Evolutionary Computation)
- **Quelle:** PDF `06_Master_Archive/04_Architecture/ALTE_Frau_95g_Neuste_Optimierungsalgorithmen_Integration_v1.0.pdf`
- **Konzept:** LLM Proposal Engine + Evolutionary Selector + hierarchisches Mutations-Gedächtnis + autonome PeerReview-Layer; Pilot für Prompt-Variationen der Campfire-Serie.
- **Status:** TEILWEISE — Scaffold `fusion_hero_os/modules/heroic_llm_ea/` (Stub-LLM, echte Fitness/Memory, 2026-07-05). Echter Provider/Campfire-Pilot offen.

### A3. tz-dev/PMS-RUST-Einbindung
- **Quelle:** V8-Strategie/Synthese
- **Status:** OFFEN (ehrlich gelabelt in `V8_STATUS_REPORT.md`). Ersatz: eigener `pms_rust_kernel` (implementiert, bewiesen).

### A4. EvolveAndPushCoreModule (v7.10) — autonomer Evolutions-/Propagations-Zyklus
- **Quelle:** `docs/99_archive/EVOLVE_AND_PUSH_v7.10.md`
- **Konzept:** 6-Track-Zyklus Evolution→Review→Archiv→Propagation (GitHub, GDrive, Vercel, Canva, Notion, "Secret Horkruxe").
- **Status:** GRÖSSTENTEILS OFFEN — als Code existieren nur die Hintergrund-Skripte (`auto_save.ps1`, `sync_grok_intern.ps1`, `sync_medienserver.ps1`, `end_session.ps1`), die Auto-Commit/Sync leisten. Der volle autonome Zyklus ist Narrativ.

### A5. Horkrux-Protokoll v7.8/v7.9 (VisualMediaHorkrux, SecretHiddenHorkrux, AndroidEmbodimentHorkrux)
- **Quelle:** `HORKRUX_MEDIA_SECRET_SYNC_v7.9.md`, `ALL_UNIFIED_VERSIONS_HORKRUX_SYNC_v7.8.md`
- **Status:** OFFEN als Code — reine Prosa. Der bewiesene Kern des Sync-Gedankens existiert als `fusion_hero_os/core/masterseed_sync.py` (mutual_sync mit Monotonie-Satz). AOSP/Android-Embodiment: keinerlei Code-Spur.

### A6. Operator-Katalog-Ausbau
- **Quelle:** `docs/04_execution/PMS_OPERATOR_CATALOG_v7.5.md`, Abschnitt "Nächste Schritte (offen, nicht begonnen)"
- **Offen:** maschinenlesbare JSON/YAML-Fassung des VOLLEN Katalogs, domänenspezifische Ketten (Buchkapitel, Legal, Beziehungen), Verlinkung Ketten ↔ `book/heroismus_v33/`.
- **Teilerfolg:** Kernbestand via `PMS.yaml` + `pms_rust_kernel --validate-chain` maschinell validierbar.

### A7. Roadmap-Säule "Core-Patent"
- **Quelle:** PDF `ALTE_Frau_95g_Roadmap_v1.0.pdf` (Säule 1: Patentierung von Selbstmodifikation, Pionier-Mechanismus, HeroicImageOrchestrator)
- **Status:** OFFEN/UNBEKANNT — kein Beleg in Repos; Abgleich mit Grok-/Claude-Konversationen aussteht (User-Auftrag 2026-07-04).

### A8. HeroicImageOrchestrator / Bildgenerierungs-Pipeline mit Rate-Limit-Orchestrator
- **Quelle:** PDFs `ALTE_Frau_95g_Bildgenerierungs_Pipeline_Rate_Limit_Loesung_v1.0.pdf`, `ALTE_Frau_95g_Real_Foto_Integration_Pipeline_v1.0.pdf`
- **Status:** TEILWEISE — Scaffold `fusion_hero_os/modules/image_orchestrator/` (Dry-Run, YAML Identity, Rate-Limiter, 2026-07-05). Echte Bild-API + mister-Contributor-gui-Anbindung offen.

---

## B. Teilweise umgesetzt

### B1. Hard Fork + Core-Verschlüsselung (MIGRATION_KONZEPT_v7.12)
- **Umgesetzt:** Privates Repo **`95guknow/fusion-hero-core` existiert** (2026-07-01): `kernel/bridge/` (C-Python-IPC: `fhos_ipc_server.c`, `fhos_ipc_client.py`) + `start_fusion_hero.py` (Unified Launcher, 6,3 KB).
- **NICHT umgesetzt:** Obfuskation/Verschlüsselung des öffentlichen Cores (PyArmor/Nuitka/Service).
- **WIDERSPRUCH zur Proprietär-Entscheidung (User 2026-07-04):** `95guknow/FuHOS_pub` ist **öffentlich** und enthält den vollen Code + alle Archive (01_Framework, 02_Mathematik, 03_Code, 04_Buch_und_Archiv, 06_Master_Archive, kernel, v2_beta, Sync-Skripte). → Entscheidung nötig: privat schalten / bereinigen / löschen.

### B2. v8-Kernel-Lücke (GitHub-Abgleich, User-Auftrag "schaue selbst nach") — GESCHLOSSEN 2026-07-04
- `fusion-hero-os` main == lokaler Stand `main-knoten-proofs` + 1 Datei (`visual_seeds/95g_Hacker_VisualSeed_Registration_v8.md`).
- Der v8-Bare-Metal-Kernel (`kernel/`: boot.s, smp/, ai/, gui/, ide/, management/, drivers/) hatte gefehlt: **`kernel/bridge/` (C-Python-IPC) + Unified Launcher** — beides lag NUR im privaten `fusion-hero-core`. Umgekehrt fehlt `fusion-hero-core` weiterhin der gesamte Bare-Metal-Kernel.
- **PORTIERT (User-Entscheidung 2026-07-04):** `kernel/bridge/fhos_ipc_server.c`, `kernel/bridge/fhos_ipc_client.py`, `kernel/bridge/README.md` und `start_fusion_hero.py` aus `fusion-hero-core` in dieses Repo übernommen. Dashboard-Pfad des Launchers (`03_Code/Dashboard/heroic_core_gui.py`) existiert hier.
- **Ehrlicher Hinweis:** Die Bridge nutzt `AF_UNIX`-Sockets + gcc — lauffähig unter Linux/WSL, NICHT nativ unter Windows-Python. Ungetestet auf dieser Maschine; Test unter WSL steht aus.

### B3. CEC / RHE / PsycholysisBreakthroughTrigger (v7.12-Extensions)
- **Quelle:** `Fusion_MasterSeed_Extensions_v7.12.md`
- **Status:** Mini-Module existieren (`fusion_hero_os/core/cec.py`, `rhe.py`, `psycholysis_trigger.py`), aber mit vereinfachten Formeln; RHE: "Vollständige Rust-Implementierung folgt später"; CEC-Kohärenz: "kann später durch QUBO ersetzt werden".

### B4. Rust-Vollmigration des Evolutionsframeworks
- **Quelle:** PDF `ALTE_Frau_95g_Migration_zu_schnellerer_Sprache_Rust_v1.0.pdf`
- **Umgesetzt:** `rust_engine_crate/` (rayon-Annealing) + `pms_rust_kernel_crate/`.
- **Offen:** asynchrones LLM-Interface (tokio+reqwest), hierarchisches Evolutionsgedächtnis (sled), Migration des Gesamtframeworks, Python↔Rust-Benchmarks.

### B5. Buch-Publishing (Roadmap-Säule 3)
- **Umgesetzt:** `04_Buch_und_Archiv/Der_Heroischer_Mensch_2026-06-15/` (CLI-EXE + Streamlit-Web-Version), Buchkonzept-PDF; Buch "Heroismus" in Arbeit (laut Grok-User-Memory).
- **Offen:** Verlinkung Operator-Ketten ↔ Buchkapitel (siehe A6); Publikations-Track.

### B6. Top-level `modules/`-Platzhalter
- `modules/alte_frau_95g/`, `mainframe_laden/`, `skill_creator/` sind leer; lauffähige Module liegen in `fusion_hero_os/modules/`. Ausbauen oder entfernen.

---

## C. Bewusst nicht umgesetzt / bereits erledigt (keine offenen Ideen)

- **SelfModifyCore:** bewusst NUR Vorschlags-Registry (Sicherheitsentscheidung, dokumentiert).
- **Erledigt & bewiesen (nicht Teil des Backlogs):** Knoten 16/17/19/20, echtes Multi-Core-Hyperthreading (`backend="auto"`), MasterSeed-Integrität (SHA-256 + K20), Phoenix-Mode-Reset, PMS-Minimal-Kernel, MasterSeed-mutual_sync.
- **VirtualGPUHTCache:** bleibt deklarierte Simulation.

---

## D. Offene Fragen & Entscheidungen (Stand 2026-07-04, User befragt)

1. **Grok-Bestand (A1/A2/A8):** User-Antwort: existieren **als Code in Grok-Projekten**. → Export-Anfrage erstellt: `docs/01_vision/GROK_EXPORT_REQUEST.md` (Grok liest dieses Repo via GitHub; Zielpfade + Anforderungen je Modul definiert). Bis zum Eingang Status OFFEN — lokal liegt nichts davon.
2. **FuHOS_pub:** User-Entscheidung: **später entscheiden**. Bleibt vorerst öffentlich; Konflikt mit Proprietär-Entscheidung bleibt dokumentiert und ungelöst.
3. **Bridge-Port:** ENTSCHIEDEN + UMGESETZT — siehe B2.
4. **Core-Patent (A7):** weiterhin ungeklärt — nur mit User-/Grok-Wissen klärbar.
5. **Gerettete Trainingsdaten (2026-07-04):** Beim Sync der Zweitkopie `C:\Users\Admin\fusion-hero-os` wurden 42 lokale 4D-Matrix-v2-Trainingszeilen aus der upstream gelöschten `data.jsonl` gesichert (`03_Code/internal_llm/data.jsonl.local-backup-2026-07-04`, 507 Zeilen). Bewertung: abgeleitete Daten — die Quell-Wissensbasis existiert hier reicher (`03_Code/core/knowledge/Geisteskrankheiten_4D_Matrix_v2–v7*.md` + `ingest_v*_training.py`). Keine Reintegration nötig; Backup bleibt als Sicherung.

---

## E. Ideenrunde 2026-07-05 — Claude-Sweep + Gemini-Synthese v9

**Quellen:** Repo-Sweep 2026-07-05 (8 Claude-Vorschläge aus Backlog + verworfenen
Ansätzen), Gemini-Deep-Research-Formalisierung („Hero Space", CRDT/Gossip,
proof_registry) — Review mit Verdicts: `docs/01_vision/GEMINI_SYNTHESIS_v9_REVIEW.md`.
**Maschinelle Verankerung:** `proof_registry.yaml` + `scripts/check_proof_registry.py` (CI-Gate).

| # | Idee | Status | Registry-Claim |
|---|------|--------|----------------|
| E1 | Beweis-Registry + CI-Gate | **UMGESETZT 2026-07-05** (21 Claims, 15 BEWIESEN ↔ 29 Tests) | — (ist die Registry selbst) |
| E2 | Sync-Kern als Join-Halbverband (CvRDT, paarweise) | **UMGESETZT 2026-07-05** (`tests/test_masterseed_semilattice.py`) | SYNC-SEMILATTICE ✅ |
| E3 | Horkrux-Gossip-Netz (N Knoten, O(log N)-Konvergenz) | OFFEN — nächster Schritt: `fusion_hero_os/core/horkrux_gossip.py` + Runden-Property-Test | GOSSIP-LOGN |
| E4 | QUBO-Scheduler für Supervisor (Pipeline TaskGraph→QUBO-Builder→parallel_anneal) | OFFEN — Benchmark vs. Heuristik ist das Erfolgskriterium; KEIN Quanten-Backend (Gemini-QPU-Teil abgelehnt) | QUBO-SCHEDULER-NUTZEN |
| E5 | Performance-Orakel (Benchmark-JSONL + Regression statt CNN) | OFFEN — liefert B4-Benchmarks mit | ORACLE-PREDICT |
| E6 | Timespace-Token-Management als MMR-QUBO (lokal, ohne Grok-Wartezeit) | OFFEN — bei Grok-Eingang (A1) gegeneinander benchmarken | TIMESPACE-QUBO |
| E7 | Ehrlicher LoRA-Track (erst versiegeltes Holdout + deterministische Eval, dann Training) | OFFEN — Ziel F1 ≥ 10 % (von 1,97 %) | LORA-F1 |
| E8 | Hörbarer Schwarm (MessageBus → tts_router, Piper-Backend) | OFFEN — Demo-Kandidat; tts_router seit 2026-07-05 importierbar | — |

**Abgelehnt (ehrlich dokumentiert, nicht vergessen):** D-Wave/QPU-Integration,
CNN/GP-Surrogate als Startpunkt, BFT-Behauptung aus CRDT allein (heruntergestuft
auf OFFEN: BFT-ROBUSTHEIT), DPP-Formalismus für v1.
