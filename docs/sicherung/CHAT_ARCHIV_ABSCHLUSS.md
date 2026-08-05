# Chat-Archiv — inaktive Sessions abschliessen und auslagern

**Modul:** `fusion_hero_os/core/conversation_session_closure.py`
**Konfiguration:** `google_one_sicherung.yaml` → `chat_archive:`
**Quelle:** `~/.grok/sessions` (Session-Speicher der Instanzen)
**Ziel:** `gs://fusion-ai-data-project-bbf0e6db-52e1-462b-8e3/chat_archives`

Das Inventar in `conversation_archive_inventory.py` erfasst, **was existiert**.
Dieses Modul ist der Schritt danach: eine Session, die seit Wochen niemand
angefasst hat, ist keine laufende Arbeit mehr — sondern ein abgeschlossenes
Gespräch, das sich nur noch wie ein offenes verhält. Der Sweep macht das
explizit und läuft unbeaufsichtigt.

## Drei Schritte

| Schritt | Was passiert | Wohin |
|---------|--------------|-------|
| **close** | Session ohne Artefakt neuer als `inactive_days` bekommt `CLOSED.json` | in die Session selbst |
| **archive** | versiegelte, noch nicht ausgelagerte Sessions → ein `.tar.gz` + `manifest.json` | `~/.fusion/sicherung/snapshots/chats_<stamp>/` |
| **transfer** | Bundle + Manifest nach Google Cloud Storage | `gs://…/chat_archives/<bundle_id>/` |

## CLI

```powershell
# Was liegt an? (aendert nichts)
python -m fusion_hero_os.core.conversation_session_closure --status
python -m fusion_hero_os.core.conversation_session_closure --list

# Vollstaendiger Plan, ohne einen einzigen Schreibvorgang
python -m fusion_hero_os.core.conversation_session_closure --dry-run

# Der Lauf: abschliessen + archivieren + nach GCS transferieren
python -m fusion_hero_os.core.conversation_session_closure

# Varianten
python -m fusion_hero_os.core.conversation_session_closure --close-only
python -m fusion_hero_os.core.conversation_session_closure --no-transfer
python -m fusion_hero_os.core.conversation_session_closure --route drive
python -m fusion_hero_os.core.conversation_session_closure --inactive-days 30
```

Kontrolle nach dem Lauf:

```powershell
gcloud storage ls gs://fusion-ai-data-project-bbf0e6db-52e1-462b-8e3/chat_archives/
```

## Konfiguration

```yaml
chat_archive:
  enabled: true
  inactive_days: 14          # Schwelle, ab der eine Session als beendet gilt
  drive_subfolder: chat_archives
  gcs_prefix: "gs://…/chat_archives"   # leer -> Drive-for-Desktop-Route
  purge_after_transfer: false
```

Laufzeit-Override des Ziels: `FUSION_CHAT_ARCHIVE_GCS`.

Der Transfer waehlt automatisch: gesetzter `gcs_prefix` → GCS
(`google-cloud-storage` → `gcloud storage cp` → `gsutil cp`, in dieser
Reihenfolge). Ohne Prefix faellt er auf den Drive-for-Desktop-Spiegel aus
`desktop.fusion_folder_documents` zurueck und verifiziert die Kopie per SHA-256.

## Was das Siegel enthaelt

`CLOSED.json` je Session: `last_activity`, `idle_days`, Schwelle, Datei- und
Byte-Zahl, Artefakt-Zaehlungen und ein SHA-256-**Fingerprint ueber den
Dateiindex** (Name, Groesse, mtime) — nicht ueber Dialoginhalte. Das ist billig
genug fuer einen 300-MB-Baum bei jedem Durchlauf und schlaegt trotzdem an, sobald
sich etwas aendert.

Das Siegel selbst zaehlt nicht zur Aktivitaet. Sonst wuerde jede geschlossene
Session im naechsten Lauf sofort wieder als aktiv gelten und nie geschlossen
bleiben.

## Idempotenz

Ein Ledger (`~/.fusion/sicherung/manifests/chat_archive_ledger.json`) haelt fest,
in welchem Bundle eine Session gelandet ist. Wiederholte Laeufe bearbeiten nur,
was seither dazugekommen ist. Bewegt sich eine Konversation nach dem Abschluss
doch noch, aendert sich ihr Fingerprint — dann wird sie erneut gebuendelt.

Der Sweep ist damit gefahrlos als wiederkehrender Job einzuplanen.

## Privacy

| Op | Gilt fuer |
|----|-----------|
| **deploy** | privat — Dialoginhalte, `.tar.gz`, Run-Manifest bleiben im Operator-Speicher |
| **push** | public — nur Zaehlungen: `docs/sicherung/last_chat_closure.summary.json` |

Dateien, deren **Name** auf ein Secret hindeutet (`.env`, `*secret*`,
`*credential*`, `*.pem`, `id_rsa*`, `push_secret*` sowie `exclude_globs` aus
`google_one_sicherung.yaml`), landen nicht im Bundle und stehen als
`secret_filtered:` in der Skip-Liste des Manifests.

**Das ist ein Dateinamen-Filter, kein Inhalts-Scan.** Ein Token, das mitten in
einem `terminal/*.log` oder in `system_prompt.txt` steht, wird davon nicht
erfasst. Wer das braucht, muss vor dem Transfer inhaltlich pruefen.

## Loeschen (`--purge`)

Standardmaessig loescht der Sweep **nichts**. Sessions bleiben liegen und tragen
zusaetzlich ihr Siegel.

`--purge` entfernt die Session-Ordner eines Bundles — aber nur, wenn der Transfer
`verified` gemeldet hat *und* das lokale Bundle noch exakt auf den im Manifest
festgehaltenen SHA-256 hasht. Beide Bedingungen muessen halten; faellt eine aus,
verweigert der Purge und meldet den Grund. Ein Gespraech, das durch eine halb
fehlgeschlagene Kopie verloren geht, ist nicht wiederherstellbar.

**Vermerk:** [MAINFRAME · Chat-Archiv · close→archive→transfer · deploy=private · push=counts]
