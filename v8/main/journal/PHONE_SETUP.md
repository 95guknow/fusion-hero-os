# Voice-Journal — Handy-Anbindung

Ziel: Das Handy nimmt Sprachnotizen auf, schickt die Transkripte an den
Journal-Server auf dem PC, und die Pipeline sortiert sie thematisch in das
Tages-Tagebuch (`journal/tagebuch/YYYY-MM-DD.md`) ein.

## Was dieses System ehrlich kann (und was nicht)

- **Kann:** Transkripte per HTTP entgegennehmen, lokal (ohne Cloud/LLM) nach
  Themen sortieren, pro Tag als Markdown-Tagebuch rendern, Duplikate
  verwerfen, Offline-Notizen per Inbox nachziehen.
- **Kann nicht:** Selbst auf dem Handy "immer zuhoeren". Die Spracherkennung
  laeuft auf dem Handy — dieses Repo liefert nur die Empfangs- und
  Sortier-Seite plus ein Termux-Script als quasi-kontinuierliche Loesung.
  Echtes Always-On (Foreground-Service, Hotword) braucht eine eigene
  Android-App — das ist hier **nicht** enthalten.

## Rechtlicher Hinweis

Dauerhaftes Mitschneiden nimmt zwangslaeufig auch Gespraeche Dritter auf.
In Deutschland ist das Aufnehmen des nichtoeffentlich gesprochenen Wortes
anderer ohne deren Einwilligung strafbar (§ 201 StGB). Das Setup ist fuer
**eigene Sprachnotizen** gedacht — in Gegenwart anderer pausieren oder deren
Einverstaendnis einholen.

## 1. Server auf dem PC starten

```powershell
$env:JOURNAL_TOKEN = "<langes-zufaelliges-token>"
python -m uvicorn journal.server:app --host 0.0.0.0 --port 8787
```

Ohne `JOURNAL_TOKEN` nimmt der Server nichts an. Handy und PC muessen sich
erreichen — gleiches WLAN reicht; unterwegs am einfachsten via
[Tailscale](https://tailscale.com) (PC + Handy ins gleiche Tailnet, dann die
Tailscale-IP des PCs als Server-Adresse nutzen). Windows-Firewall: Port 8787
fuer eingehende Verbindungen freigeben (privates Netz).

Test vom Handy-Browser: `http://<pc-ip>:8787/journal/health`

## 2. Handy-Optionen (aufsteigend nach Aufwand)

### Option A — Termux-Loop (quasi-kontinuierlich, im Repo enthalten)

1. **Termux** und **Termux:API** aus F-Droid installieren (Play-Store-Version
   ist veraltet und inkompatibel).
2. In Termux: `pkg install termux-api curl jq`
3. Script aufs Handy kopieren (`journal/phone/termux_voice_loop.sh`), dann:
   ```bash
   export JOURNAL_SERVER=http://<pc-ip>:8787
   export JOURNAL_TOKEN=<token>
   bash termux_voice_loop.sh
   ```
4. Akku-Optimierung fuer Termux + Termux:API deaktivieren, sonst wuergt
   Android die Schleife im Hintergrund ab.

Grenzen: Android-STT arbeitet sessionweise (endet nach Sprechpause), die
Schleife startet sofort neu — es entstehen kurze Luecken. Offline-Notizen
werden lokal gepuffert und nachgeliefert.

### Option B — MacroDroid / Tasker (Diktat auf Knopfdruck oder Trigger)

Makro: Trigger (Widget-Knopf, Kopfhoerer-Taste, "Handy geschuettelt", …)
→ Aktion "Spracheingabe" → Aktion "HTTP Request":

- Methode POST, URL `http://<pc-ip>:8787/journal/note`
- Header: `Content-Type: application/json`, `X-Journal-Token: <token>`
- Body: `{"text": "[Sprachumwandlung]", "source": "macrodroid"}`

Zuverlaessiger als Option A und akkuschonend — dafuer nicht kontinuierlich,
sondern pro Ausloesung eine Notiz. Fuer den Alltag meist die beste Wahl.

### Option C — Beliebige Diktier-App + Inbox (ganz ohne Server)

Transkripte als JSONL-Datei in `journal/inbox/` ablegen (z.B. via Syncthing
oder manuell), eine Zeile pro Notiz:

```json
{"text": "Idee fuer den QUBO-Solver ...", "ts": "2026-07-05T14:30:00", "source": "handy"}
```

Dann auf dem PC: `python -m journal.pipeline` — arbeitet alles ein und
verschiebt die Dateien nach `inbox/processed/`.

## 3. Ergebnis

Pro Tag entsteht `journal/tagebuch/YYYY-MM-DD.md` mit Themen-Abschnitten
(Gesundheit, Projekt & Code, Ideen & Erkenntnisse, …) und Zeitstempel +
Tagesabschnitt (Morgen/Mittag/Nachmittag/Abend/Nacht) pro Eintrag. Themen
und Keywords sind in `journal/config.yaml` anpassbar. Alles unterhalb der
`<!-- MANUELL: ... -->`-Zeile in der Tagebuch-Datei bleibt beim automatischen
Neu-Rendern erhalten — dort kann von Hand weitergeschrieben werden.
