# Offenlegung — Betrieb, Forschung, Gedankenspiel

> **Stand:** v15.0.0 · 2026-08-01
> Öffentliches Dokument. Gilt für dieses Repository, die Landing Page und alle
> Publikationen der Senfkorn UG zu Fusion Hero OS.

Dieses Projekt vermischt drei Dinge, die nicht dasselbe sind: **laufende
Software**, **Forschungsvorhaben** und ein **Gedankenspiel**. Wer hier ankommt,
liest Begriffe wie *MasterSeed*, *Horkrux*, *Layer 6 ω*, *BIG ALPHA*,
*Ascension*. Ohne Einordnung klingt das nach Produktbehauptungen. Es sind
keine.

Dieses Dokument zieht die Trennlinie und benennt, was auf welcher Seite steht —
auch dort, wo das unbequem ist.

---

## Wer schreibt

**Senfkorn UG** (haftungsbeschränkt) · Operator und Autor: **Stephan Hagen Urban**.

Fusion Hero OS ist Eigenentwicklung. Es wird nicht als Produkt verkauft, nicht
lizenziert und nicht als Dienstleistung angeboten. Es gibt keine Kunden, keine
Nutzerkonten, keine Datenverarbeitung für Dritte.

> **Offen:** Ein vollständiges Impressum mit Handelsregister-Daten und
> ladungsfähiger Anschrift gehört auf die öffentliche Fläche und ist hier noch
> nicht hinterlegt. Bis dahin ist dieses Dokument eine inhaltliche Offenlegung,
> kein Impressum im Sinne des DDG.

---

## Die drei Schichten

### 1. Betrieb — läuft und ist geprüft

Software, die tatsächlich ausgeführt wird und deren Verhalten durch Tests
gedeckt ist. Aktuell **703 Tests** in der Suite; die CI führt sie bei jedem PR
aus.

| Was | Wo |
|---|---|
| QUBO-Solver, Simulated Annealing, Parallel-Anneal | `fusion_hero_os/engine/`, `qb_qubo.py` |
| Zitterpolymesh — DAG-Scheduler über vier Lanes | `fusion_hero_os/core/zitterpolymesh.py` |
| Versions-Gate (Manifest-Konsistenz) | `scripts/bump_version.py --check` |
| Code-Honesty-Gate (Claims gegen echte Tests) | `scripts/check_proof_registry.py` |
| PII-Scanner, blockierend in CI | `scripts/check_pii_scanner.py` |
| Push-Guard (verhindert ungewollte Pushes) | `fusion_hero_os/core/push_layer_guard.py` |
| Öffentlich/Privat-Trennung des MasterSeed | `fusion_hero_os/core/masterseed_public.py` |

### 2. Forschung — ladbar, nicht betriebsbereit

Code, der existiert und importiert werden kann, dessen Aussagen aber nicht
belegt sind. Vor allem `ascension_os/` (AscensionOS v9.x). Das ist als
**Roadmap** geführt, nicht als Funktion.

### 3. Gedankenspiel — Rahmen, kein Befund

Die mythische Ebene. Sie ist bewusst gewählt, sie trägt die Arbeit, und sie ist
**keine Tatsachenbehauptung**:

- **MasterSeed M_0''''**, **Horkrux**, **Layer 6 ω**, **Sisyphos-Zyklus**,
  **BIG OMEGA / BIG ALPHA** — Begriffe eines selbstgebauten Ordnungssystems.
  Sie beschreiben, wie das Werk gegliedert ist, nicht was die Software kann.
- **„Dissertation-as-OS"** — die These, das Betriebssystem *sei* die Arbeit,
  ist eine ontologische Setzung des Autors. Sie ist **keine Aussage über einen
  akademischen Status**. Das Wort „Dissertation" bezeichnet hier die Form des
  Werks; ein verliehener Grad, ein laufendes Promotionsverfahren oder eine
  betreuende Institution werden damit weder behauptet noch in diesem
  Repository dokumentiert. Die Textfassung ist auf Academia.edu
  selbstveröffentlicht — das ist eine Publikation, keine Begutachtung.
- **Identity Preservation Score**, **Strict Contraction Property über alle
  Layer** — Modellsprache. Diese Größen werden nicht gemessen.
- **„Ära"-Namen** von Plattformversionen (etwa v14 „Poly-Mesh /
  n-dimensionale Mannigfaltigkeit") sind Richtungsangaben. Die zugehörigen
  Behauptungen stehen offen in der Proof Registry.

---

## Was hier ausdrücklich **nicht** behauptet wird

**Kein Quantencomputer.** Die QPU-Lane ist immer simuliert. Das Repo sagt das
selbst: *„immer `virtual: true` — es ist kein echter Quantenprozessor
angebunden"* (`zitterpolymesh.md`). Jeder Lauf gibt pro Lane `backend` und
`virtual` aus.

**Keine medizinische oder psychologische Leistung.** Die Kompendien
*Geisteskrankheiten in der 4D-Matrix* und *Psychogramm* sind Modell- und
Reflexionstexte. Sie stellen keine Diagnose, ersetzen keine ärztliche,
psychotherapeutische oder psychiatrische Behandlung und richten sich an
niemanden als Patienten. **Bei akuter Gefährdung gilt klinische
Standardversorgung vor jeder Modellinterpretation.** Die Dokumente führen diese
Grenze selbst und ausführlich.

**Keine offensive Sicherheitsarbeit.** Der Rahmen ist ausdrücklich
`labor_sandkasten`, `offense: FORBIDDEN`, `sandbox_only: true`
(`alpha_meister_hasch.seal.json`). „Cybersecurity" meint hier Orientierung und
Härtung der eigenen Flächen — keine Dienstleistung, keine Angriffe, kein
Pentesting für Dritte.

**Keine Anlage-, Rechts- oder Steuerberatung.** Auch nicht dort, wo
Kostenfunktionen, Businessplan oder On-Chain-Skripte im Repo liegen.

**Keine KI mit Eigenleben.** „Self-Modification" bedeutet in diesem Projekt
Parameteranpassung, nicht Selbstveränderung von Code. Vorschläge werden
gesammelt, nicht angewendet; wirksam wird ein Diff erst, wenn ein Mensch ihn
committet. Das Modul sagt es selbst: *„Es gibt hier keinen Mechanismus für
unbeaufsichtigte Laufzeit-Selbstmodifikation."*
(`fusion_hero_os/modules/self_modify.py`)

Auch der Begriff **„evolve"** gehört hierher: er ist ein Kommandowort an ein
Sprachmodell, keine ausführbare Operation. Es gibt kein `evolve`-Kommando im
Projekt — die Änderungen schreibt danach ein Mensch oder ein Assistent unter
Aufsicht, und sie durchlaufen dieselbe CI wie alles andere.

---

## Wie man das nachprüft

Die **Proof Registry** (`proof_registry.yaml`) ist die maßgebliche Instanz. Sie
führt jede Systembehauptung mit einem von drei Zuständen:

| Status | Bedeutung |
|---|---|
| **BEWIESEN** | Durch mindestens einen real existierenden Test gedeckt. Maschinell erzwungen. |
| **OFFEN** | Hypothese. Darf in Dokumenten nur als solche zitiert werden. |
| **WIDERLEGT** | Durch Gegenbeispiel gefallen. Bleibt stehen, statt gelöscht zu werden. |

**Stand heute: 67 Behauptungen — 52 bewiesen, 13 offen, 2 widerlegt.**

`scripts/check_proof_registry.py` prüft, dass jede BEWIESEN-Behauptung auf
einen Test zeigt, den es wirklich gibt. Eine Behauptung ohne Test kann nicht
als bewiesen eingetragen werden.

---

## Was gerade widerlegt ist

Zur vollen Offenlegung gehört, die eigenen Fehlschläge zu nennen, nicht nur die
Erfolge. Beide Einträge stammen vom 2026-08-01:

**`GATE-BLOCKIERT-MERGE-TATSAECHLICH`** — Die Dokumentation behauptete, kein
Merge nach `main` sei ohne zwei unabhängige menschliche Bestätigungen möglich
und *„Automation (inkl. Claude) merged nie selbst"*. Tatsächlich wurde PR #105
per API gemergt, während die Google-Bestätigung offen stand und keine
Review-Freigabe vorlag. Ursache: die Schranke war nie als Required Check
eingetragen. Der Mechanismus war intakt, die Durchsetzung fehlte.

**`V15-ZWEI-AEREN-OHNE-RELEASE`** — Das Versionsschema erklärt den annotierten
Git-Tag zur Quelle der Wahrheit. Tatsächlich steht `VERSION` auf 15.0.0,
während das letzte veröffentlichte Release `v13.0.0` ist. Für zwei
aufeinanderfolgende Hauptversionen gilt die eigene Regel nicht.

Beide sind offen dokumentiert und behoben, sobald die jeweilige Einstellung
gesetzt beziehungsweise getaggt ist.

---

## Warum das so dasteht

Ein Werk, das mit *Horkrux* und *Layer 6 ω* arbeitet, kann leicht wie eine
Behauptung über die Welt gelesen werden. Es ist eine Behauptung über die
**Form** dieser Arbeit.

Die Trennung wird deshalb nicht dem Lesenden überlassen. Sie steht in der
Registry, sie wird in der CI geprüft, und sie steht hier.

Die Designvorlage des Werks formuliert dieselbe Regel für den Text:
**keine Metapher-als-Beweis.** Dieses Dokument ist ihre Anwendung auf das
Projekt als Ganzes.

---

**Verbindlich:** `proof_registry.yaml` · `BEST_VERSION.md` ·
`docs/kompendium/V3.3_DESIGNVORLAGE_VERBINDLICH.md`
