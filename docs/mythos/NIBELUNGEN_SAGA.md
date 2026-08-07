# Nibelungen-Saga — Stack-Erweiterung

**Stand:** 2026-08-07 · **Platform:** Fusion Hero OS v13.0.0  
**Quellen (Public Domain / gemeinfrei):** *Nibelungenlied* (mhd.), nordische Parallelen (*Völsunga saga*, *Edda*-Stoffe) — **Narrative Referenz**, kein juristischer Anspruch auf eine einzelne Edition.  
**Policy:** labor · public-safe · no vault · no_external_targets

---

## 1. Zweck im OS

Die Nibelungen-Saga erweitert **Mythos5** um ein **Heldenepos-Organ**:

- Initiation (Drachenkampf → Siegfried-Moment)  
- Macht & Hort (Vault vs. Public)  
- Tarnkappe (Cloak)  
- Treue, Verrat, Konsequenz (Governance, Consent, Threat Model)  
- Untergang / Omega (Integritätsbogen schließen) vs. Alpha (neuer Zyklus)

Sie **ersetzt** weder Fable5 noch CI noch den MasterSeed.

---

## 2. Kernfiguren → Rollenmap

| Figur / Kraft | Saga-Funktion | Stack-Mapping | Geltung |
|---------------|---------------|---------------|---------|
| **Siegfried** | Held, Drachentöter, Tarnkappen-Träger | Held / Heroic Core / public-safe Speer-Träger | Modell |
| **Kriemhild** | Bindung, später Rache-Ökonomie | Expression-Membrane · Langzeitgedächtnis des Unrechts (Ledger) | Modell |
| **Gunther** | König / Hof-Autorität | Operator-Governance · Branch-Strategie · Release-Tags | Modell |
| **Hagen** | Treue zum Hof, Speer gegen Lindenblatt | Threat / Insider-Risiko · ehrliche Schwäche ausnutzen | Modell (defensiv benannt) |
| **Brühild** | Probe, Ehre, Wettkampf | PeerReview · Human-Confirm · „Probe vor Bindung“ | Modell |
| **Alberich / Nibelungen** | Hort-Hüter, Zwergenmacht | Vault-Layer · MasterSeed-Shards · fail-closed | Modell |
| **Drache (Fafnir-Analog)** | Hort-Wächter, Drachenhaut | Opacity / Abwehr-Haut vor public Expression | Modell |
| **Tarnkappe** | Unsichtbarkeit / Stärke im Nibelungenlied | **Hypertarnkappe** (Policy + Lens) | Spezifikation (Name + Docs) |
| **Hort** | Gold, Macht, Fluch | Private Vault — **nie** git-public | Spezifikation |
| **Worms** | Öffentlicher Hof | Clearweb / GitHub / `95guknow.github.io` | Modell |
| **Etzel / Ende** | Katastrophe, Omega | Session-Close · Seal · Integritätsbogen | Modell |

---

## 3. Handlungsbögen (6) — Kompendium-kompatibel

Analog zu den 6 Bögen des Public-UI-Stub / Heroismus-Manuskripts:

| Bogen | Saga | Labor-OS |
|-------|------|----------|
| **I Initiation** | Drachenkampf, Blut, Haut | Siegfried-Moment · Speer durch Drachenhaut |
| **II Werkzeug** | Tarnkappe, Schwert | Hypertarnkappe · Hyperpanzerknacker (lab) |
| **III Hof** | Worms, Werbung, Eide | Public Mesh · Coworking-KI · Branch-Strategie |
| **IV Riss** | Betrug, doppelte Wahrheit | Code Honesty · keine Dual-Review-Fiktion |
| **V Speer** | Lindenblatt / Verrat | Threat Model · Lindenblatt benennen, nicht leugnen |
| **VI Omega/Alpha** | Untergang / Nachhall | BIG OMEGA sealed · BIG ALPHA open |

---

## 4. Motive (operativ)

### 4.1 Tarnkappe ≠ Lüge

Im Lied gibt die Tarnkappe **Macht und Unsichtbarkeit**.  
Im Stack: **Hypertarnkappe** verbirgt *Vault und PII*, nicht die **Versionswahrheit**.  
Public Pol darf (und soll) klar sagen: v13.0.0 · Alpha open · labor only.

### 4.2 Hort-Fluch

Macht ohne Consent und ohne Integrity-Distanz zieht den Untergang.  
**BCG + MasterSeed-Kontraktion:** Evolution nähert sich dem Fixpunkt, statt den Hort in die Public-Fläche zu schleppen.

### 4.3 Lindenblatt-Doktrin

Jeder „unverwundbare“ Claim braucht eine **explizite Schwachstellen-Notiz**.  
Siehe: honesty notes in Fable5/Mythos5 Summaries.

### 4.4 Hyperpanzerknacker

Nicht „Hagen gegen den Hof“, sondern **defensive Property-Probe** am eigenen Sandkasten — analog x402 sandbox audits.

---

## 5. Quellen & Lesepfade (gemeinfrei / Orientierung)

| Stoff | Hinweis |
|-------|---------|
| Nibelungenlied | Mittelhochdeutsch; moderne Übersetzungen je nach Verlag (Textwahl operator-lokal) |
| Völsunga saga | Nordische Siegfried/Sigurd-Parallele (Fafnir, Hort) |
| Edda (Auszüge) | Motiv-Hintergrund, nicht kanonischer OS-Beweis |

**Repo speichert:** Mapping, Geltung, Checklisten — **nicht** eine urheberrechtlich geschützte Volltext-Edition eines modernen Verlags als „unsere“.

---

## 6. Integration

| Artefakt | Pfad |
|----------|------|
| Siegfried-Moment | [SIEGFRIED_MOMENT.md](SIEGFRIED_MOMENT.md) |
| Grimm-Ergänzung | [GRIMM_MAERCHEN_VOLLAUSGABE.md](GRIMM_MAERCHEN_VOLLAUSGABE.md) |
| YAML-Map | [nibelungen_grimm_map.yaml](nibelungen_grimm_map.yaml) |
| Modul | `fusion_hero_os/core/nibelungen_mythos.py` |

---

## 7. Honesty footer

Nibelungen-Erweiterung = **Mythos-Organ + Vokabular + Governance-Spiegel**.  
Kein Anspruch: Saga-Treue als mathematischer Satz.  
Kein Anspruch: Realraum-Handlung nach Epos.
