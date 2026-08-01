# Human Confirm Gate — 2x externe Handy-Auth vor jedem Merge

> **Stand:** v14.0.0 · 2026-08-01

## ⚠️ Durchsetzungsstatus zuerst

Dieses Dokument beschreibt einen **Mechanismus**, keine geltende Garantie.
Ob er bindet, hängt an genau einer Einstellung außerhalb dieses Repos:
`human-confirm/google` muss in den **Required Checks** der Branch Protection
stehen. Steht es dort nicht, ist alles Folgende ein Hinweis-Kommentar —
**das Gate ist dann nicht erzwungen**, und GitHub lässt den Merge zu,
während der Check pending steht.

**Belegter Gegenfall — 2026-08-01:** PR
[`95guknow/fusion-hero-os#105`](https://github.com/95guknow/fusion-hero-os/pull/105)
wurde per API gemergt, während `human-confirm/google` offen stand (das Secret
`GOOGLE_CONFIRM_WEBAPP_URL` war nicht gesetzt, der Check also dauerhaft
pending). Die API meldete `mergeable_state: unstable` — nicht `blocked` —
und der Merge ging durch. Weder eine GitHub-Review-Approval noch eine
Google-Bestätigung lagen vor. Die Formulierung „Automation merged nie selbst"
stand zu diesem Zeitpunkt als Tatsache in diesem Dokument und war falsch.

Prüfe den Status, bevor du dich darauf verlässt:

```bash
gh api repos/95guknow/fusion-hero-os/branches/main/protection \
  --jq '.required_status_checks.contexts'
```

Erscheint `human-confirm/google` in der Liste, bindet das Gate. Sonst nicht.

## Prinzip

Vorgesehen ist: kein Merge nach `main` oder `ascension` ohne **zwei
unabhängige, externe Bestätigungen vom Handy**:

1. **GitHub** — PR-Review-Approval, in der Praxis per GitHub-Mobile-App
   (Passkey/Biometrie beim Freischalten).
2. **Google** — der `human-confirm/google`-Check, gekippt durch eine
   Apps-Script-Web-App unter deinem eigenen Google-Account
   (`scripts/google_confirm_webapp/`) — Google-Sign-In ist die Schranke,
   nicht ein Passwort im Repo.

Die Absicht dahinter: Automation — inklusive Claude — soll nicht selbst
mergen. Sie öffnet PRs, lässt CI laufen, postet die zwei Bestätigungslinks.

Dass sie es *nicht kann*, folgt aber nicht aus dieser Absicht, sondern
ausschließlich aus der Branch Protection. Was der Workflow selbst garantiert,
ist enger und in `tests/test_human_confirm_gate_workflow.py` festgehalten:
er kann den Check **öffnen**, aber nicht **schließen**. Das ist notwendig,
nicht hinreichend.

## Ablauf pro PR

1. PR wird geöffnet (von Claude oder jedem anderen Contributor).
   **Entwürfe werden übersprungen** — ein Draft kann ohnehin nicht gemergt
   werden. Das Gate öffnet erst, wenn der PR auf „ready for review" geht.
2. `.github/workflows/human-confirm-gate.yml` öffnet einen **pending**
   Check-Run `human-confirm/google` und pflegt **genau einen** PR-Kommentar
   mit den zwei Links. Jeder weitere Push aktualisiert diesen Kommentar,
   statt einen neuen anzulegen. Falls `PHONE_NOTIFY_WEBHOOK_URL` gesetzt ist,
   kommt eine Android-Push-Notification mit beiden Links als Tap-Actions
   (nutzt die bestehende `tailscale_phone_notify.py`-Infrastruktur/ntfy.sh) —
   **nur beim Öffnen, Wiederöffnen und „ready for review"**, nicht bei jedem
   Folge-Push.
3. Du tippst am Handy:
   - **GitHub-Link** → Review öffnen → Approve.
   - **Google-Link** → öffnet die Apps-Script-URL im Browser → Google fragt
     nach Sign-in (falls nicht schon angemeldet) → Script patcht den
     Check-Run auf `success`.
4. Sind **beide** grün und alle CI-Checks grün, gibt Branch Protection den
   „Merge"-Button frei — **sofern `human-confirm/google` als Required Check
   eingetragen ist**. Fehlt der Eintrag, blockiert nichts; der pending Check
   erzeugt dann nur `mergeable_state: unstable` statt `blocked`, und der
   Merge ist trotzdem möglich (siehe Durchsetzungsstatus oben).

Die Bestätigung ist an den Commit gebunden (`sha` steckt in der Confirm-URL).
Ein neuer Push setzt sie deshalb zurück — das ist der Sinn der Schranke, nicht
ein Fehler.

**Fehlt das Secret `GOOGLE_CONFIRM_WEBAPP_URL`, bleibt der Check offen.** Das
ist Absicht: fehlende Einrichtung darf die Schranke nicht stillschweigend
öffnen. Der PR-Kommentar weist einmalig darauf hin und wird bei weiteren
Pushes nur aktualisiert.

Ein offener Check blockiert den Merge allerdings **nur dann**, wenn er
required ist. Ohne diesen Eintrag ist der Effekt genau umgekehrt: die fehlende
Einrichtung fällt gar nicht auf, weil gemergt werden kann, als wäre nichts.
Am 2026-08-01 war exakt das der Fall.

## Einmalige Einrichtung (musst du selbst machen — kein Tool-Zugriff von hier)

### 1. Google Apps Script deployen

Siehe [`scripts/google_confirm_webapp/README.md`](../../scripts/google_confirm_webapp/README.md).
Ergebnis: eine Web-App-URL, hinterlegt als Repo-Secret
`GOOGLE_CONFIRM_WEBAPP_URL`.

### 2. Repo-Secrets setzen

GitHub → `95guknow/fusion-hero-os` → Settings → Secrets and variables →
Actions → New repository secret:

| Secret | Wert | Pflicht? |
|---|---|---|
| `GOOGLE_CONFIRM_WEBAPP_URL` | Apps-Script-Web-App-URL aus Schritt 1 | ja |
| `PHONE_NOTIFY_WEBHOOK_URL` | z. B. `https://ntfy.sh/<dein-privates-topic>` | optional, sonst nur PR-Kommentar |
| `PHONE_NOTIFY_TOKEN` | Bearer-Token für privates ntfy-Topic | optional |

**Secrets werden nicht über Forks oder Spiegel hinweg vererbt.** Läuft der
Workflow auch in einem Spiegel-Repository (etwa `Senfkorn-UG/fusion-hero-os`),
muss `GOOGLE_CONFIRM_WEBAPP_URL` dort separat gesetzt werden — sonst bleibt das
Gate dort dauerhaft offen und der Merge blockiert. Alternativ den Workflow im
Spiegel deaktivieren, wenn dort gar nicht nach `main` gemergt werden soll.

### 3. Branch Protection aktivieren

GitHub → Settings → Branches → **Add rule** (für `main`, dieselbe Regel
separat für `ascension`):

- Branch name pattern: `main`
- ☑ Require a pull request before merging
  - Require approvals: **1**
- ☑ Require status checks to pass before merging
  - Suchen und auswählen: **`human-confirm/google`**
  - plus die bestehenden CI-Checks, die schon Pflicht sein sollen
    (`ci (3.11, light)`, `pii-scan`, `build (3.11)`, `build (3.12)`, …)
- ☑ Do not allow bypassing the above settings (inkl. Administratoren, wenn
  du willst, dass die Regel auch für dich selbst ausnahmslos gilt)
- ☐ **Allow force pushes** — aus lassen
- ☐ **Allow deletions** — aus lassen

Das ist der Schritt, der „komplett extern" tatsächlich **erzwingt** — ohne
ihn ist alles oben nur ein Hinweis-Kommentar, kein Gate. Ich habe dafür
keinen API-Zugriff (Repo-Admin-Settings sind nicht Teil der verfügbaren
GitHub-Tools) — das musst du im UI einmalig klicken.

## Sicherheitsdesign — was trägt und was nicht

**In diesem Repo beweisbar** (`tests/test_human_confirm_gate_workflow.py`,
Registry-Claim `GATE-WORKFLOW-KANN-SICH-NICHT-SELBST-FREIGEBEN`):

- Der GitHub-`GITHUB_TOKEN` im Workflow kann den `human-confirm/google`-Check
  **öffnen**, aber nicht **schließen** (kein `conclusion` im Workflow-Code) —
  nur der Apps-Script-Endpoint mit deinem separaten, eng gescopten PAT kann das.
- Der Workflow beansprucht weder `administration` noch `workflows`-Rechte,
  könnte die Schranke also nicht selbst umkonfigurieren.
- Das Apps-Script-PAT hat ausschließlich `Checks: Read/Write` — es kann
  keinen Code pushen, keine Branches ändern, keine Secrets lesen.

**Nicht in diesem Repo beweisbar** (Registry-Claim
`GATE-BLOCKIERT-MERGE-TATSAECHLICH`, Status `OFFEN`):

- Ob ein Merge wirklich blockiert wird. Das ist Server-State bei GitHub, kein
  Repo-Inhalt — kein Test hier kann es zeigen, und am 2026-08-01 war es
  nachweislich nicht der Fall.

Der frühere Satz „warum das nicht umgehbar ist" stand über einer Liste, die
das nie belegt hat: alle drei Punkte beschreiben, was der *Workflow* nicht
kann. Umgangen wurde das Gate aber nicht über den Workflow, sondern daran
vorbei — durch einen direkten Merge-Aufruf, den Branch Protection nicht
abgewiesen hat. Gegen diesen Weg schützt ausschließlich der Required-Check-
Eintrag, nicht die Token-Scopes.

Und selbst mit korrekter Konfiguration gilt: die Schranke bindet Automation,
die sich an sie hält, plus alles, was GitHub serverseitig durchsetzt. Wer
Repo-Admin ist, kann sie jederzeit abschalten — deshalb ist „Do not allow
bypassing" unten kein Detail, sondern der Punkt, an dem die Regel auch für
dich selbst gilt.

## Reichweite

Gilt für **jeden** Merge nach `main`/`ascension` — auch für die
main→ascension-Propagation, die bisher per Direct-Push lief. Die läuft ab
sofort ebenfalls über einen PR mit diesem Gate, nicht mehr über
`git push origin ascension`.

## Related

- Workflow: `.github/workflows/human-confirm-gate.yml`
- Google-Auth-Bein: `scripts/google_confirm_webapp/`
- Push-/Merge-Vokabular: `docs/ops/DEPLOY_PUSH_MERGE.md`
- Push-Klassifizierung: `push_layer_guard.yaml`
- Branch-Modell: `BRANCH_STRATEGY.md`
