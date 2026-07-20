# Human Confirm Gate — 2x externe Handy-Auth vor jedem Merge

> **Stand:** v12.0.0 · 2026-07-20

## Prinzip

Kein Merge nach `main` oder `ascension` ohne **zwei unabhängige, externe
Bestätigungen vom Handy**:

1. **GitHub** — PR-Review-Approval, in der Praxis per GitHub-Mobile-App
   (Passkey/Biometrie beim Freischalten).
2. **Google** — der `human-confirm/google`-Check, gekippt durch eine
   Apps-Script-Web-App unter deinem eigenen Google-Account
   (`scripts/google_confirm_webapp/`) — Google-Sign-In ist die Schranke,
   nicht ein Passwort im Repo.

Automation — inklusive Claude — **merged nie selbst**. Sie öffnet PRs,
lässt CI laufen, postet die zwei Bestätigungslinks. Der Merge-Button bleibt
ausschließlich in deiner Hand, extern gegenüber diesem Repo.

## Ablauf pro PR

1. PR wird geöffnet (von Claude oder jedem anderen Contributor).
2. `.github/workflows/human-confirm-gate.yml` öffnet einen **pending**
   Check-Run `human-confirm/google` und postet einen PR-Kommentar mit zwei
   Links. Falls `PHONE_NOTIFY_WEBHOOK_URL` gesetzt ist, kommt zusätzlich eine
   Android-Push-Notification mit beiden Links als Tap-Actions (nutzt die
   bestehende `tailscale_phone_notify.py`-Infrastruktur/ntfy.sh).
3. Du tippst am Handy:
   - **GitHub-Link** → Review öffnen → Approve.
   - **Google-Link** → öffnet die Apps-Script-URL im Browser → Google fragt
     nach Sign-in (falls nicht schon angemeldet) → Script patcht den
     Check-Run auf `success`.
4. Erst wenn **beide** grün sind **und** alle CI-Checks grün sind, lässt
   GitHub Branch Protection den „Merge"-Button überhaupt zu.

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

## Sicherheitsdesign (warum das nicht umgehbar ist)

- Der GitHub-`GITHUB_TOKEN` im Workflow kann den `human-confirm/google`-Check
  **öffnen**, aber nicht **schließen** (kein `conclusion: success` im
  Workflow-Code) — nur der Apps-Script-Endpoint mit deinem separaten,
  eng gescopten PAT kann das.
- Das Apps-Script-PAT hat ausschließlich `Checks: Read/Write` — es kann
  keinen Code pushen, keine Branches ändern, keine Secrets lesen.
- Selbst wenn beide Tokens kompromittiert würden, verlangt Branch Protection
  zusätzlich die echte GitHub-Review-Approval — zwei unabhängige Systeme
  müssen beide fallen, nicht nur eins.

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
