# Coworking-KI in GitHub — Setup und Grenzen

**Stand:** v1.0 · 2026-07-24
**Workflow:** `.github/workflows/claude-coworking.yml`
**Gate:** `tests/test_coworking_workflow.py` · Proof-Registry-Anker `COWORKING-KI-NO-SELF-MERGE`

---

## Das Problem, das dieser Workflow löst

Vor dem 2026-07-24 hatte das Repo **genau einen** KI-Touchpoint: `summary.yml` fasst
neue Issues einmalig zusammen (`actions/ai-inference@v1`). Das ist eine Einbahnstraße —
man konnte aus GitHub heraus **nicht** mit einer KI zusammenarbeiten: keine Rückfrage,
kein Patch auf Zuruf, kein Review auf Anfrage. Jede KI-Arbeit musste außerhalb von
GitHub stattfinden und von Hand zurückgetragen werden.

Dieser Workflow schließt die Lücke: **`@claude` in einem Issue- oder PR-Kommentar**
startet einen Lauf, der im Thread antwortet und bei Bedarf einen Branch mit Änderungen
aufmacht.

## Setup (nur der Operator kann das)

1. API-Key auf <https://console.anthropic.com> erzeugen.
2. Im Repo: **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `ANTHROPIC_API_KEY`
   - Wert: der Key
3. Fertig. Ab dem nächsten `@claude`-Kommentar läuft der Workflow.

> **Ohne dieses Secret bleibt die Coworking-KI bewusst wirkungslos.** Der Workflow
> postet dann einen ehrlichen Hinweis und beendet sich mit Erfolg — er täuscht
> keinen Erfolg vor und scheitert nicht still. Dasselbe Muster nutzt der
> `PHONE_NOTIFY_WEBHOOK_URL`-Step in `human-confirm-gate.yml`.

## Nutzung

| Ort | Beispiel |
|-----|----------|
| Issue-Kommentar | `@claude schau dir bitte den Fehler in layer_registry an` |
| PR-Kommentar | `@claude review diesen Diff gegen die Geltungsmarken-Regel` |
| Review-Kommentar | `@claude kannst du das hier fixen?` |
| Neues Issue | `@claude` im Body, oder Label `claude` setzen |

## Harte Grenzen (maschinell geprüft)

| Regel | Warum | Durchsetzung |
|-------|-------|--------------|
| **Kein Selbst-Merge, kein Selbst-Approve** | `human-confirm-gate.yml`: „Automation (inkl. Claude) merged diesen PR nicht selbst — komplett extern." Merge braucht zwei unabhängige menschliche Bestätigungen. | `test_workflow_contains_no_merge_or_approve_call` + Branch Protection |
| **Ehrliche Degradation ohne Secret** | Code-Honesty-Kultur: kein Fake-Erfolg | `test_workflow_has_honest_secret_guard` |
| **Begrenzte Permissions** | Kein `administration`, kein `workflows: write` (sonst könnte der Lauf sein eigenes Gate umschreiben) | `test_workflow_permissions_are_bounded` |
| **Nur bei Ansprache** | Nicht jeder Kommentar startet einen Lauf | `if:`-Bedingung auf `@claude`, getestet |
| **Ein Lauf pro Issue/PR** | Race-Guard; laufende Patches werden nicht mitten im Schreiben abgebrochen | `concurrency`-Gruppe, `cancel-in-progress: false` |

Zusätzlich bekommt die KI die Repo-Doktrin per `prompt` mit: Proof-Registry-Regel
(kein BEWIESEN ohne grünen Testknoten), Geltungsmarken, PII-Verbot für dieses
öffentliche Repo, Kollisionsprüfung vor neuen Namen (A13).

## Ehrlicher Status

- Geprüft ist die **Workflow-Struktur** (YAML, Trigger, Guard, verbotene Aufrufe,
  Permissions). **Nicht** geprüft ist das Laufzeitverhalten der Action — das hängt
  von GitHub, dem Secret und dem Modell ab und ist in pytest nicht testbar.
- Der Workflow ersetzt kein Review. Was die KI im Thread produziert, unterliegt
  denselben Gates wie jeder andere Beitrag (CI, Proof Registry, PII-Scan,
  Zwei-Faktor-Merge).
- `summary.yml` bleibt unverändert bestehen — die beiden kollidieren nicht
  (verschiedene Trigger, verschiedene Zwecke).
