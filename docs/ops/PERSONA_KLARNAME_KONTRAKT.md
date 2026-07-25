# Persona- und Klarnamen-Kontrakt

**Stand:** v1.0 · 2026-07-25
**Grundlage:** ausdrückliche Operator-Entscheidung vom 2026-07-25
**Durchsetzung:** `tests/test_persona_scanner.py`, `tests/test_asset_persona_paths.py`, `scripts/check_pii_scanner.py`

---

## Die Entscheidung

> Die Persona-Bezeichnungen bleiben bestehen. Der **Klarname steht im Vordergrund.**

Damit ist der frühere Stage-A/Stage-B-Kurs — vollständige Tilgung der Persona-Token aus
dem Baum — **nicht mehr die geltende Absicht**. Die entsprechenden Gates hielten die CI
auf `main` dauerhaft rot, ohne einen echten Defekt anzuzeigen: sie prüften einen Vertrag,
den es so nicht mehr gibt.

## Was jetzt gilt

| Ebene | Regel | Gate |
|-------|-------|------|
| **Klarname** | Primäre öffentliche Identität. Wird vom PII-Scanner **nicht** als Finding behandelt (dort greifen nur E-Mail, IPs, MagicDNS, Tokens, Keys). | — |
| **Persona im Inhalt** | Erlaubt, aber **eingedämmt**: nur in den dokumentierten, bekannten Dateien. Eine neue Datei mit der Schreibweise fällt durch. | `test_persona_spelling_stays_within_known_files` |
| **Persona in Pfaden** | Weiterhin **verboten**. Datei- und Verzeichnisnamen sind die öffentlich sichtbare Oberfläche (URLs, Verzeichnislisten, Klon-Ausgaben). | `test_no_persona_token_in_tracked_paths` |
| **Persona in `fusion_hero_os/`** | Nur in den Dateien, deren **Gegenstand** die Identität ist. Überall sonst im aktiven Paket bleibt es eine Regression. | `test_active_package_is_persona_free_outside_identity_files` |
| **Echte PII / Secrets** | Unverändert blockierend: private E-Mail, IPv4, MagicDNS, Tailscale-Authkeys, API-Tokens, Private Keys. | `check_pii_scanner.py`, `pii-scan.yml` |

## Warum Eindämmung statt Freigabe

Ein Gate ersatzlos zu streichen hätte die CI ebenfalls grün gemacht — aber jede künftige
Ausbreitung der Persona wäre unbemerkt geblieben. Beide Tests behalten deshalb ihre
Schutzwirkung und tragen eine **explizite, begründete Ausnahmeliste**. Wer eine Datei
hinzufügt, muss die Aufnahme bewusst vornehmen; zusätzlich prüfen
`test_persona_content_allowlist_has_no_dead_entries` und
`test_persona_subject_files_still_exist`, dass die Listen nicht auf gelöschte Pfade
zeigen und so still erodieren.

## Bekannte Fundstellen (Stand v1.0)

**Persona-Schreibweise im Inhalt** — vier Dateien:

- `.grok/skills/mainframe-laden/SKILL.md` und `01_Framework/skills/mainframe-laden/SKILL.md`
  — Protokollname in der Modulliste (zwei Spiegel derselben Skill-Datei).
- `business/STEPHAN_HAGEN_URBAN_BUSINESS_PERSONA_PUBLICATION.md` und
  `business/auto_recognition_stephan_hagen_urban.py` — nennen die Persona ausschließlich
  als **Negativ-Regel** („nur implizit heroisch – keine explicit …"), also gerade um sie
  aus geschäftlicher Kommunikation herauszuhalten. Genau hier ist der Klarname bereits
  im Vordergrund.

**Retiriertes Core-Token in `fusion_hero_os/`** — zwei Dateien:

- `fusion_hero_os/core/comaedchen_identity.py` — das Modul beschreibt und exportiert
  diese Identität; das Token dort zu streichen würde es inhaltlich aushöhlen.
- `fusion_hero_os/registry.py` — eine Zeile, die Registry-Beschreibung ebendieses Moduls.

## Ehrlicher Status

Dieser Kontrakt regelt **Benennung und Sichtbarkeit**, nicht Sicherheit. Er lockert an
keiner Stelle den Schutz vor echten Geheimnissen oder personenbezogenen Daten Dritter —
die blockierenden Scanner-Regeln bleiben unverändert. Die Entscheidung, den eigenen
Klarnamen öffentlich zu führen, ist die des Operators und gilt nur für ihn selbst.
