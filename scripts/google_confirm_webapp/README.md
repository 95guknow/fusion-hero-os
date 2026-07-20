# Google Confirm Web App

> **Stand:** v12.0.0 · 2026-07-20

Das Google-Auth-Bein des `human-confirm/google`-Merge-Gates. Läuft **nicht**
in diesem Repo — es ist eine [Google Apps Script][gas] Web App, die der
Operator unter seinem eigenen Google-Account deployt. Vollständige
Einrichtung: [`docs/ops/HUMAN_CONFIRM_GATE.md`](../../docs/ops/HUMAN_CONFIRM_GATE.md).

[gas]: https://script.google.com

## Dateien

- `Code.gs` — der eigentliche `doGet`-Handler (Google-Identität prüfen →
  GitHub-Check-Run auf `success` patchen).
- `appsscript.json` — Deployment-Manifest: `access: MYSELF`,
  `executeAs: USER_DEPLOYING`. Das ist die eigentliche Google-Auth-Schranke —
  Google verweigert den Aufruf bereits vor `Code.gs`, wenn der Anrufer nicht
  der deployende Account ist.

## Deploy (einmalig)

1. [script.google.com](https://script.google.com) → neues Projekt.
2. Inhalt von `Code.gs` einfügen (ersetzt den Default-`Code.gs`-Stub).
3. Project Settings → Script Properties → hinzufügen:
   - `GITHUB_TOKEN` — Fine-grained PAT, Repository access: nur
     `fusion-hero-os`, Permissions: **Checks: Read and write** (sonst nichts —
     kann damit weder pushen noch mergen noch Secrets lesen).
   - `ALLOWED_GOOGLE_EMAIL` — deine Gmail-Adresse.
4. Deploy → New deployment → Web app → Execute as: **Me** → Who has access:
   **Only myself** → Deploy.
5. Web-App-URL kopieren, als Repo-Secret `GOOGLE_CONFIRM_WEBAPP_URL` in
   `fusion-hero-os` hinterlegen (Settings → Secrets and variables → Actions).

Damit ist der Google-Auth-Leg fertig; GitHub-Branch-Protection-Setup steht
in `docs/ops/HUMAN_CONFIRM_GATE.md`.
