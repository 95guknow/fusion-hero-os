# A13 — Brainstorm-Vokabular: Herkunft, Kollisionen, Operationalisierung

**Paket:** Gemini-Brainstorm 2026-07-24 (extern) → `ascension_os/core`, `fusion_hero_os/core`, `artifacts/fractal_ghost_hunt`
**Designvorlage:** Kompendium der Heroik V3.3 — keine Metapher als Beweis
**Stand:** v2.1 · 2026-07-24 (v2.0: drei Bausteine + Kollisionen · v2.1: Stub-Liquidation, Coworking-KI, zwei weitere Neuprägungen)

---

## Synthese

Am 2026-07-24 entstand in einer externen Gemini-Session ein umfangreiches Vokabular für das ascensionOS: „Layer 0 als externer Host", „SSH Hugging Handshake", „n±2 Ghosthunting", „Placebo-Optimierung / Nocebo-Minimierung", „Sprungfeder-Loops / Raceloops", „M-pression", „uQuBO-i", „Imaginations-M-vers", „hyper-meta-qubernate.manifold.nD". Dieser Anhang gibt dem Vokabular seinen ehrlichen kanonischen Ort: **drei** Bausteine werden zu Spezifikation befördert (echter Code, echte Tests, Proof-Registry-Claims), der Rest wird als Modell oder Fragment markiert — und **drei Namenskollisionen** mit bereits existierendem, getestetem Code werden explizit dokumentiert, damit die Doktrin „Wiring + De-Dup vor Re-Import" (`artifacts/2026-07-16_legacy_ghost_hunt.md`) nicht verletzt wird.

Axiomatisches Prinzip dieser Operationalisierung (v2.0): **jeder beförderte Baustein trägt einen sichtbaren Axiom-Anker** — einen Proof-Registry-Claim, dessen Testknoten in CI laufen. Was keinen Anker hat, bleibt Modell/Fragment und wird nie als Betriebsbehauptung zitiert.

---

## Bogen 1 — Glossar mit Geltungsmarken

**[Definition]** Arbeitsdefinitionen aller Brainstorm-Begriffe. Die Geltungsmarke bezeichnet den Status des BEGRIFFS, nicht seines etwaigen Code-Ablegers.

| Begriff | Herkunft | Arbeitsdefinition | Geltung |
|---------|----------|-------------------|---------|
| Layer 0 (externer Host) | Brainstorm | Externe, unkorrumpierbare Intentions-Instanz außerhalb des operativen Stacks | **Fragment** (Kollision, Bogen 2) |
| SSH Hugging Handshake | Brainstorm | Kryptographisch gesicherte Übergabe von Intention an das gedockte System | **Modell** (operationalisiert Bogen 4 — ohne SSH/Netz) |
| n±2 Ghosthunting | Brainstorm | Prüfung des Über-über-/Unter-unter-Nachbarn statt nur der Adjazenz | **Modell** (operationalisiert Bogen 3 — bewusst nicht „ghosthunt" genannt) |
| M-pression | Brainstorm | Informations-/Reibungsverlust bei der Projektion latent → manifest | **Modell** (operationalisiert Bogen 5 als Projektionsverlust) |
| Placebo-Optimierung | Brainstorm | Senkung der „Aktivierungsenergie" erwünschter Zustände | **Modell** — keine Engine, kein Beweis |
| Nocebo-Minimierung | Brainstorm | Entfernen nicht-verifizierter, außen-induzierter Constraints | **Modell** — als Analogie zur bestehenden Code-Honesty-Praxis lesbar |
| Sprungfeder-Loop | Brainstorm | Akkumulation in einer Ebene, dann sprunghafter Ebenenwechsel | **Fragment** (Kollision, Bogen 2) |
| Raceloop | Brainstorm | Hochfrequente Iteration strikt innerhalb einer Ebene | **Modell** — deckungsgleich mit bestehenden Iterationsschleifen, kein neuer Mechanismus |
| uQuBO-i | Brainstorm | „unconstrained Quantizing unconstrained Binaries Optimierung im Imaginations-M-vers" | **Fragment** — der echte QUBO-Solver (`qb_qubo.py`) bleibt die einzige Kanon-Quelle |
| Imaginations-M-vers | Brainstorm | n-dimensionaler Möglichkeitsraum latenter Potenziale | **Fragment** — keine formale Definition, kein Code |
| hyper-meta-qubernate.manifold.nD | Brainstorm | „Root-Befehl" der Gesamtarchitektur | **Fragment** — Name, kein Objekt |
| n-D Mannigfaltigkeit / Faserbündel | Brainstorm | Differentialgeometrische Rahmung des latenten Raums | **Fragment** — Metapher; es existiert keine Mannigfaltigkeits-Struktur im Code |
| `hypersafecall.sync` | Brainstorm (2026-07-24) | „sicherer Auto-Update-Ruf" | **Fragment** — null Treffer im Repo. Die reale Entsprechung existiert bereits: `fusion_hero_os/modules/hero_autoupdate.py` + `hero_autoupdate.yaml` (1-Min-Polling, 5-Min-Reminder, Android-Notify). Kein neues Modul — De-Dup-Doktrin. |
| `hypertarnkappe` | Brainstorm (2026-07-24) | „gesteigerte Tarnkappe" | **Fragment** — der reale `tarnkappe`-Layer in `fusion_unified.yaml` ist `docs-only`; eine „Hyper"-Steigerung hätte keinen zusätzlichen Gegenstand. |

---

## Bogen 2 — Namenskollisionen (Doktrin: Wiring + De-Dup vor Re-Import)

**[Spezifikation]** Drei Brainstorm-Begriffe landen auf Namen, die im Repo bereits mit **anderer** Bedeutung real belegt und getestet sind:

| Begriff | Bereits belegt durch | Bedeutung dort |
|---------|----------------------|----------------|
| **Layer 0** | `01_Framework/SKILL.md` (Core Layer Architecture) | Immutable Foundation (Prinzipien-Schicht) |
| **Layer 0** | `docs/02_architecture/HEROIC_CORE_ORCHESTRATOR.md` | `MasterSeed` (Banach-Fixpunkt-Konzept) |
| **Ghosthunt / Geisterjagd** | `ascension_os/core/geisterjagd_module.py` | Banach-Fixpunkt-Konvergenz latent → manifest |
| **Ghosthunt / Geisterjagd** | `src/normal_os/ascension/ghosthunt_hook.py` (getestet in `tests/test_suite_integration.py`) | Koevolutionäre Heuristik-Brücke zwischen den suite/layers 00–07 |
| **Sprungfeder / Springloop** | `qb_qubo.py::springloop_energy` | Gedämpfte Gradienten-Relaxation als QUBO-Heuristik |

**[Fragment]** Keine der bestehenden Bedeutungen ist „Skip-eine-Ebene-Crosscheck" oder „Akkumulation-dann-Ebenensprung". Konsequenz dieser Operationalisierung: **keine dritte Bedeutung auf besetzte Namen.** Der n±2-Crosscheck heißt `layer_distance_crosscheck` (nicht „ghosthunt"), der Handshake heißt `root_anchor_handshake` (nicht „Layer 0"), und „Sprungfeder" bleibt unbenutzt. Die Brainstorm-Begriffe werden hier als Herkunft zitiert — im Code tragen sie kollisionsfreie Namen.

---

## Bogen 3 — Operationalisierung 1: n±2 als Graph-Distanz-Crosscheck

**[Spezifikation]** `fusion_hero_os/core/layer_distance_crosscheck.py` — reine BFS-Graphmathematik auf dem echten Layer-Graphen (`fusion_unified.yaml` `layer_edges`).

| Funktion | Rolle |
|----------|-------|
| `build_adjacency(layer_edges)` | Ungerichtete Adjazenz aus den Kanten-Dicts |
| `distance_n_neighbors(adjacency, start, n)` | Exakte Kürzeste-Pfad-Distanz-n-Menge (BFS) |
| `find_blind_spot_candidates(adjacency, health, origin)` | origin + Distanz-1 healthy, Distanz-2 nicht → Kandidat |
| `crosscheck_all` / `crosscheck_real_layers` | Alle Knoten / echter Graph mit `present ∧ config_ok` als Health |

**[Satz]** Axiom-Anker `LAYER-DISTANCE-CROSSCHECK` (Proof Registry, BEWIESEN): BFS-Distanzsemantik exakt; Distanz-1- und Distanz-2-Mengen disjunkt auf Pfad-Fixture UND echtem Graphen. Zwei hand-verifizierte Beispiele: `knowledge` hat Distanz-1 = {kernel, ascension, intelligence, connectors, vr} und Distanz-2 = **{orchestration}**; `tarnkappe` hat Distanz-1 = {network} und erreicht **android** erst auf Distanz 2 — Knoten, die reine Adjazenz-Prüfung nie sieht. Der Crosscheck läuft über den vollständigen 16-Layer-Graphen inklusive der Poly-Mesh-Schichten (network, connectors, file_share, service_coordination) und tarnkappe.

**[Modell]** Die Design-Rationale „Skip-eine-Ebene-Prüfung fängt korrelierte blinde Flecken benachbarter Ebenen" bleibt Modell — plausibel, nicht bewiesen.

---

## Bogen 4 — Operationalisierung 2: RootAnchorHandshake

**[Spezifikation]** `ascension_os/core/root_anchor_handshake.py` — Ed25519 Sign/Verify über kanonisches JSON-Manifest (`cryptography`-Bibliothek; Präzedenz: `crypto_identity.py`).

| Funktion | Rolle |
|----------|-------|
| `canonical_bytes(manifest)` | Deterministische Byte-Form (sort_keys, kompakte Separatoren) |
| `generate_keypair` / `AnchorKeyPair` | Prozess-lokales Ed25519-Paar (keine Schlüsseldatei als Seiteneffekt) |
| `sign_manifest` / `verify_manifest` | Hex-Signatur; Verify fail-closed (False statt Exception) |
| `RootAnchorHandshake` | Klassen-Wrapper für Sign+Verify |

**[Satz]** Axiom-Anker `ROOT-ANCHOR-TAMPER-DETECT` (BEWIESEN): jede Abweichung von Manifest, Signatur oder Public Key → False; Schlüssel-Reihenfolge im Dict irrelevant.

**[Ehrlich]** Kein SSH-Protokoll, kein Netzwerk-Handshake, keine Verdrahtung mit MasterSeed/Foundation-Runtime. Das „Hugging" bleibt Bild; die Integritätsprüfung ist real.

---

## Bogen 5 — Operationalisierung 3: M-pression als Projektionsverlust

**[Spezifikation]** `ascension_os/core/mpression_projection.py` — `measure_mpression(v, basis)` misst `loss = ‖v − Pv‖` mit dem bewiesenen K17-Orthogonalprojektor (`heroic_math_engine.OrthogonalProjector`), Wiederverwendungs-Konvention wie `geisterjagd_module.py`.

**[Satz]** Axiom-Anker `MPRESSION-PROJECTION-LOSS` (BEWIESEN) + `K17`: Pythagoras-Identität hält numerisch (Residuum < 1e-9), Verlust 0 gdw. v im Unterraum, `relative_loss ∈ [0,1]` (Nicht-Expansivität K17d).

**[Modell]** Die Deutung „v = Intention, span(U) = manifestierbarer Unterraum, loss = M-pression" ist Modell. Das Modul macht den Begriff **berechenbar**, nicht **wahr**.

---

## Bogen 6 — Nicht operationalisiert + De-Ghosting des Telemetrie-Stubs

**[Fragment]** Bewusst NICHT gebaut, je mit Grund:

- **uQuBO-i als neue Optimierungs-Engine** — `qb_qubo.py` bleibt die einzige Kanon-Quelle (De-Dup-Doktrin); eine zweite „QUBO-Variante" ohne neue Mathematik wäre ein Duplikat mit größerem Namen.
- **n-D-Mannigfaltigkeits-/Faserbündel-Formalismus** — es existiert kein Objekt im Code, das die Axiome einer Mannigfaltigkeit erfüllt; eine Formalisierung ohne Substanz wäre Metapher-als-Beweis.
- **`hyper-meta-qubernate.manifold.nD` als Root-Kommando** — Name ohne definierte Semantik; als Epigraph/Vokabel zulässig, als Systemobjekt nicht.
- **Placebo-/Nocebo-Engine** — die ehrliche Entsprechung existiert bereits als Praxis: Proof-Registry-Gate (entfernt nicht-verifizierte Claims = „Nocebo-Minimierung") und Geltungsmarken-Disziplin. Eine eigene „Erwartungs-Engine" hätte keinen messbaren Gegenstand.

**[Spezifikation]** De-Ghosting (v2.1 vollständig): alle **drei** Geister aus `artifacts/fractal_ghost_hunt/` (Legacy Ghost Hunt 2026-07-16, P3/Research) sind befüllt:

| Datei | v1 | v2.0 |
|-------|-----|------|
| `streamlit_hyper4d_app.py` | 88-Byte-Stub | Telemetrie-Dashboard, ausschließlich ECHTE Daten, Axiom-Anker je Panel |
| `drehbuch.md` | 72-Byte-Zeile | 5-Szenen-Storyboard, Szenen 2–4 an reale Module gebunden (Crosscheck, Banach-Geisterjagd) |
| `Hyper4D_CoEvolutionary_Morphs_FusionHeroOS.html` | 62-Byte-Versprechen | echter self-contained Tesserakt (16 Ecken/32 Kanten, Doppelprojektion 4D→3D→2D, zwei Rotationsebenen), **ohne** CDN/Libraries — löst das v1-Versprechen ehrlich ein |

Die Zufallsmetrik-Vorlage aus dem Brainstorm („np.random als M-pression") wurde verworfen: simulierte Werte als Telemetrie anzuzeigen wäre exakt die epistemische Regression, gegen die dieses Repo gebaut ist. `streamlit`/`plotly` bleiben optionale Dependencies außerhalb von `requirements.txt`.

**[Satz]** Registry-Stub-Liquidation: die Registry führte `builder_profile`, `mainframe_laden` und `skill_creator` längst als echte Pakete („wired P1"), nur `tests/test_registry.py` hielt noch den alten Stub-Zustand fest und schlug fehl. Der Test ist auf den realen Stand nachgezogen und um einen **Regressions-Guard** ergänzt, der „alle Stubs befüllt" maschinell prüfbar macht statt zu behaupten. Anker: `REGISTRY-NO-STUBS`. Die 184 vom Dependency-Atlas gezählten Platzhalter-Marker bleiben bewusst unangetastet — es sind ehrlich deklarierte Offline-Stubs (Repo-Kultur, laut Atlas-Docstring nicht fatal); sie „zu befüllen" hieße, Fallbacks durch Fake-Implementierungen zu ersetzen.

**[Satz]** Coworking-KI: Das Repo besaß keinen interaktiven KI-Workflow (einziger Touchpoint war die Einbahnstraße `summary.yml`). `.github/workflows/claude-coworking.yml` schließt die Lücke — `@claude` in Issue-/PR-Kommentaren. Die Nie-Selbst-Merge-Doktrin aus `human-confirm-gate.yml` und die ehrliche Degradation ohne `ANTHROPIC_API_KEY` sind maschinell gesichert (`COWORKING-KI-NO-SELF-MERGE`); Setup und Grenzen in `docs/ops/COWORKING_KI_GITHUB.md`. Geprüft ist die Workflow-**Struktur**, nicht das Laufzeitverhalten der Action.

**[Spezifikation]** Workflow-Kollision liquidiert: `fusion-hero-build.yml` („CI/CD Master Matrix") war ein Duplikat der konsolidierten CI (gleiche Trigger, gleiche Matrix, Test-Teilmenge). Ihr einziger Unique-Value (`pyright`) und ihr Test-Teilsatz wurden in `fusion-hero-os-ci.yml` übernommen — der Teilsatz gezielt auf Check-Level *light*, wo sonst kein `pytest` läuft —, danach wurde sie entfernt. Fortsetzung der in Issue #26 dokumentierten Konsolidierung (4 Workflows → 1); dies war der übersehene fünfte.

---

## Anhang A13 — Minimalbeispiel (Spezifikation)

```python
from fusion_hero_os.core.layer_distance_crosscheck import (
    build_adjacency_from_fusion_unified, distance_n_neighbors, crosscheck_real_layers,
)
from ascension_os.core.root_anchor_handshake import RootAnchorHandshake
from ascension_os.core.mpression_projection import measure_mpression

# 1) n±2 auf dem echten Layer-Graphen
g = build_adjacency_from_fusion_unified()
print(distance_n_neighbors(g, "knowledge", 2))   # {'orchestration'}
print(crosscheck_real_layers())                  # [] bei gesundem Graphen

# 2) Root-Anchor: signieren + Manipulation erkennen
anchor = RootAnchorHandshake()
manifest = {"layer": "ascension", "claim": "healthy"}
sig = anchor.sign(manifest)
assert anchor.verify(manifest, sig)
assert not anchor.verify({**manifest, "claim": "compromised"}, sig)

# 3) M-pression: Projektionsverlust auf die x/y-Ebene
r = measure_mpression([1.0, 2.0, 3.0], [[1, 0], [0, 1], [0, 0]])
print(r.loss)  # 3.0 — exakt die orthogonale Komponente
```

**Vermerk:** [MAINFRAME · V3.3 · Dissertation-as-OS · A13 v2.0 · Axiom-Anker verpflichtend]
