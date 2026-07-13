# Gemini-Synthese v9 — Review & ehrliche Übernahme-Entscheidungen

**Erstellt:** 2026-07-05 (Claude, nach User-Share)
**Quelle:** Gemini-Deep-Research-Bericht „Formale Architektur und wissenschaftliche Integrität:
Ein vereinheitlichtes Modell für quanten-klassische Systemorchestrierung"
(https://share.gemini.google/YQaNDEnmIhJH → gemini.google.com/share/044acc746216)
**Kontext:** Der Bericht ist Geminis Formalisierung der 8 Ideen aus dem Repo-Sweep 2026-07-05
(Claude-Vorschläge: Horkrux-Gossip, QUBO-Scheduler, LoRA-Track, Beweis-Registry,
Timespace-QUBO, PMS-Kette, Kosten-Orakel, Audio-Schwarm).

**Regel dieses Dokuments:** Jede Gemini-Aussage bekommt ein Verdict —
ÜBERNOMMEN / ANGEPASST / ABGELEHNT / OFFEN — mit Begründung. Kein Konzept wird
durch Nacherzählen zu Substanz. Maschinell verankert ist der Stand in
`proof_registry.yaml` (CI-Gate: `scripts/check_proof_registry.py`).

---

## 1. Hero Space H = (L, M, S, E) — ANGEPASST übernommen

Geminis Meta-Modell: latenter Raum L (Hypothesen), manifester Raum M (verifizierte
Zustände), Sync-Operator S (Join-Halbverband), Energiefunktion E (QUBO-Hamiltonian).

**Ehrliche Einordnung:** Das ist Terminologie, keine neue Mathematik — aber
*nützliche* Terminologie, weil sie exakt die bestehende Hauskultur formalisiert:

| Hero-Space-Komponente | Existierendes Gegenstück im Repo |
|---|---|
| L (latent, unbewiesen) | `proof_registry.yaml` status: OFFEN |
| M (manifest, bewiesen) | `proof_registry.yaml` status: BEWIESEN + grüne CI |
| S (Join-Halbverband) | `masterseed_sync.mutual_sync` — jetzt bewiesen als Halbverband (SYNC-SEMILATTICE) |
| E (QUBO-Energie) | `qb_qubo.py`, `engine/mainframe.parallel_anneal`, `mining_qubo` |

Der Übergang L→M ist bei uns wörtlich implementiert: ein Claim wechselt den
Status erst, wenn ein pytest-Knoten ihn deckt und das CI-Gate grün ist.

## 2. Beweis-Registry (proof_registry.yaml) — ÜBERNOMMEN und UMGESETZT

Geminis wichtigster Punkt, deckungsgleich mit Claude-Idee 4. **Seit 2026-07-05
implementiert:** `proof_registry.yaml` (21 Claims: 15 BEWIESEN ↔ 29 Testknoten,
6 OFFEN) + `scripts/check_proof_registry.py` + CI-Step in `ci.yml`.

**Abweichungen von Geminis Maximalversion (bewusst):**
- Kein DAG kausaler Abhängigkeiten in v1 (`depends_on` ist vorgesehen, aber
  nicht erzwungen) — erst einführen, wenn ein realer Claim ihn braucht.
- Property-Based Testing: wir nutzen deterministische numpy-Sweeps im Hausstil
  statt `hypothesis`/`proptest` — gleiche Beweisidee, keine neue Abhängigkeit.
  Shrinking wäre der Grund zu wechseln, wenn Sweeps erste Gegenbeispiele finden.
- Doc-Scan (Markdown-Claims gegen Registry prüfen) ist v2 — im Checker ehrlich
  als „bewusst NICHT Teil von v1" dokumentiert.

## 3. Distributed Sync Graph (CRDT + Gossip statt Horkrux) — KERN ÜBERNOMMEN, REST OFFEN

Geminis stärkster inhaltlicher Beitrag: Der Horkrux-Ersatz ist ein
zustandsbasierter CvRDT auf einem Join-Halbverband, Konvergenz via CALM-Theorem.

- **BEWIESEN (neu):** Der paarweise Merge von `mutual_sync` erfüllt die drei
  Halbverband-Axiome — kommutativ, assoziativ, idempotent
  (`tests/test_masterseed_semilattice.py`, Claim SYNC-SEMILATTICE). Damit ist
  der CvRDT-Kern keine Behauptung mehr. Monotonie, Identitätserhalt und
  Fail-Closed waren bereits bewiesen (SYNC-MONOTONIE, SYNC-IDENTITY, SYNC-FAILCLOSED).
- **OFFEN (ehrlich):** Die N-Knoten-Gossip-Aussage „O(log N) Runden" (Claim
  GOSSIP-LOGN). Sie ist plausibel (Epidemik-Standardresultat), aber hier erst
  bewiesen, wenn `horkrux_gossip.py` existiert und ein Test die Rundenzahl
  gegen die log-Schranke misst.
- **ABGELEHNT in Geminis Formulierung:** „Sicherheit gegen byzantinische
  Knoten". CRDT-Monotonie allein ist **kein** BFT — Äquivokation/Omission
  erfordern Signaturen und ein Adversarial-Modell. Bewiesen ist bei uns nur
  fail-closed gegen Hash-Manipulation. In der Registry als BFT-ROBUSTHEIT
  OFFEN geführt, mit heruntergestufter Notiz. Geminis eigene Passage verstößt
  hier gegen das Anti-Metaphern-Programm, das sie predigt.

## 4. QUBO-Scheduler-Pipeline — STRUKTUR ÜBERNOMMEN, QUANTEN-TEIL ABGELEHNT

Die Pipeline **Supervisor → TaskGraph → QUBO-Builder → parallel_anneal** ist
die richtige Formalisierung von Claude-Idee 2 (Task-Zuweisung strukturgleich zu
`mining_qubo`-Profit-Switching). Penalty-Terme für Constraints: Standard und korrekt.

**ABGELEHNT:** Alles ab „D-Wave Advantage / QPU / Quantum Module / hybride
quantenmechanische Solver". **Dieses Repo hat kein Quanten-Backend.**
`parallel_anneal` ist Simulated Annealing auf CPU (numba/Rust-rayon). Die
QPU-Passagen sind für uns Prosa ohne Substrat — exakt die Sorte Überclaim, die
das Honesty-Gate verhindern soll. Registry-Claim QUBO-SCHEDULER-NUTZEN ist
OFFEN mit messbarem Erfolgskriterium (schlägt die Heuristik auf synthetischen
Workloads) statt mit Quanten-Vokabular.

## 5. Performance-Orakel — IDEE ÜBERNOMMEN, DIMENSIONIERUNG ANGEPASST

Datengetriebenes Laufzeitmodell statt Heuristik: ja (deckt sich mit Claude-Idee 7,
VirtualGPUHTCache→Orakel). **ABGELEHNT als Startpunkt:** CNNs auf QUBO-Matrizen
und Gaussian-Process-Surrogate. Erst die einfache Basislinie: log-lineare
Regression auf (n, steps, n_restarts, backend) aus realen Benchmark-JSONL-Läufen.
Komplexere Modelle nur, wenn die Basislinie nachweislich versagt (Claim
ORACLE-PREDICT, OFFEN — liefert nebenbei die in B4 offenen Python↔Rust-Benchmarks).

## 6. Timespace-Token-Management als MMR-QUBO — ÜBERNOMMEN als Spezifikation

Geminis Formel ist exakt die Struktur von `make_diversity_qubo`:

    E(x) = -λ · Σ U_i·x_i  +  (1-λ) · Σ S_ij·x_i·x_j

(U = Nutzwert linear, S = Ähnlichkeits-/Redundanzstrafe quadratisch). Das
bestätigt Claude-Idee 5: lokal umsetzbar, ohne auf den Grok-Export zu warten.
DPP/k-DPP-Theorie: interessante Referenz, für v1 nicht nötig. Claim
TIMESPACE-QUBO OFFEN mit Benchmark-Pflicht (Cache-Hit-Rate vs. Kosten gegen
Recency-Heuristik). Trifft der Grok-Export doch ein: gegeneinander benchmarken.

## 7. LoRA-Track-Depriorisierung — ÜBERNOMMEN

Geminis Reihenfolge (erst Daten-Pipeline, deterministische Eval, kryptografisch
versiegeltes Holdout — dann Training) deckt sich mit dem Claude-Science-Audit
(Prio 2/3 vor Prio 1). Konkretisierung für uns: Holdout-Split aus den 507
Samples per SHA-256 versiegeln (Hash im Repo, Datei ausserhalb der
Trainingspfade), Eval-Skript als CI-Artefakt. Claim LORA-F1 OFFEN mit dem
messbaren Ziel F1 ≥ 10 % (von 1,97 %).

## 8. PMS-Kette & Audio-Schwarm — EINPASSUNG OK, EIN SACHFEHLER

- **Sachfehler bei Gemini:** „PMS = Predictive Maintenance / Monitoring State"
  ist eine Fehldeutung. PMS ist hier der **PMS-Operator-Katalog**
  (`PMS.yaml` + `pms_rust_kernel --validate-chain`). Geminis *Funktion* —
  Telemetrie-Feedback ins Orakel — ist trotzdem sinnvoll und bleibt als
  Ausbaustufe des Orakels notiert (pms_audit.jsonl existiert bereits als Spur).
- Audio-Schwarm als Sub-Graph mit derselben MMR-QUBO-Logik: elegante
  Vereinheitlichung von Claude-Idee 8, Status unverändert (Demo-Kandidat,
  `tts_router` ist seit 2026-07-05 importierbar).

## 9. Konsolidierte Prioritäten (Stand 2026-07-05)

1. ~~Beweis-Registry + CI-Gate~~ ✅ **UMGESETZT** (dieser Commit)
2. ~~Halbverband-Beweis des Sync-Kerns~~ ✅ **UMGESETZT** (SYNC-SEMILATTICE)
3. Gossip-Modul `horkrux_gossip.py` + O(log N)-Property-Test → schließt GOSSIP-LOGN
4. QUBO-Scheduler-Pilot (TaskGraph→QUBO-Builder) + Benchmark vs. Heuristik → QUBO-SCHEDULER-NUTZEN
5. Benchmark-JSONL + Regressions-Orakel → ORACLE-PREDICT (+ B4-Benchmarks)
6. Timespace-MMR-QUBO-Prototyp → TIMESPACE-QUBO
7. LoRA-Fundament (versiegeltes Holdout, deterministische Eval) → dann LORA-F1

**Nicht übernehmen, bis sich die Faktenlage ändert:** QPU/D-Wave-Integration,
CNN-Surrogate, BFT-Behauptungen, DPP-Formalismus.
