# Realwelt-Kontakt-Guard — nur der Mensch bedient das Handy

> **Stand:** v12.0.0 · 2026-07-20

## Prinzip

Kein automatisiertes Zwischenrouten bei Telefonaten oder Nachrichten mit
echten Kontakten. Nur der Mensch bedient das Handy und bestätigt jeden
Eingriff, der mit der echten Welt aus seinen Kontakten besteht — Automation
(inkl. Claude) darf so etwas weder auslösen noch dafür Mittelsmann spielen.

Das ist ein **hardcodiertes** Policy-Flag, keine Einstellung:
`fusion_hero_os.integrations.phone_link.reader.NO_INTERMEDIARY_ROUTING = True`
— nicht über Env/Config umschaltbar.

## Umsetzung

- **`fusion_hero_os/integrations/phone_link/reader.py`** — `FORBIDDEN_ACTIONS`
  (feste Denyliste: `send_message`, `send_sms`, `reply`, `forward_message`,
  `place_call`, `dial`, `call`, `answer_call`, `end_call`) +
  `deny_realworld_contact_action()`, das immer `RealWorldContactBlocked`
  wirft. `PhoneLinkReader.SEND_CAPABLE = False` ist die dazugehörige,
  introspektierbare Invariante — die Klasse besitzt und wird nie eine
  Sende-/Anruf-Methode besitzen (per Test erzwungen).
- **`fusion_hero_os/modules/phone_link.py`** — `PhoneLinkCoreModule.process()`
  prüft `FORBIDDEN_ACTIONS` als **allererstes**, vor jeder Action-
  Verzweigung. Selbst wenn später jemand versehentlich einen Sende-Pfad
  ergänzt, greift dieser Guard zuerst — Umgehen erfordert das explizite,
  reviewbare Löschen der Prüfung, kein versehentliches Feature-Hinzufügen.
- Aktuell einziger betroffener Kanal: **Phone Link** (Microsoft, lokale
  SQLite-Spiegel, ohnehin nur lesend). Repo-weite Suche nach
  Twilio/VoIP/dial/send_sms-Integrationen ergab keine weiteren Treffer
  (2026-07-20) — der Guard ist der kanonische Ansatzpunkt für jeden
  zukünftigen Telefonie-/Messaging-Kanal.

## Tests

`tests/test_phone_link.py` — Policy-Flag, fehlende Sende-Methoden
(Introspektion), jede `FORBIDDEN_ACTIONS`-Action wirft
`RealWorldContactBlocked`, Read-Only-Actions bleiben unberührt.

## Related

- `fusion_hero_os/meta/consent.py` — dasselbe Fail-Closed-Muster
  (`ConsentError`, „Authorisierungs-Check ist das einzige Gate") für
  personenbezogene Datenverarbeitung; dieser Guard ist das Pendant für
  Realwelt-Kontaktaktionen.
- `docs/ops/HUMAN_CONFIRM_GATE.md` — dasselbe Grundprinzip auf der
  Merge-Pipeline: Automation löst nichts Endgültiges gegenüber der echten
  Welt aus, ohne dass ein Mensch es am Gerät bestätigt.
