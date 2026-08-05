# Public-Safe UI-Stub · 95guknow.github.io

**Werk:** Öffentliche Orientierungsfläche (UI-Stub)  
**Ort:** `web/95guknow.github.io/ui-stub/` → https://95guknow.github.io/ui-stub/  
**Plattform-Bezug:** Fusion Hero OS **v13.0.0** (operativer Kanon im Repo; die Website **führt** ihn nicht aus)  
**Designvorlage:** [V3.3_DESIGNVORLAGE_VERBINDLICH.md](V3.3_DESIGNVORLAGE_VERBINDLICH.md) — **zwingend**  
**Policy:** public-safe only · kein Vault · Labor Frame · `connect-src 'none'`  
**Status:** Spezifikation + ausgelieferter Stub im Repo

---

## Synthese

Der UI-Stub ist die **ehrliche Attrappe** des öffentlichen Poles: Er zeigt, *wie* die duale Lesart (heroisch / formalmathematisch) und die Mesh-Orientierung **aussehen** dürfen, ohne je vorzugeben, ein Mainframe zu *sein*.

**Kernthesen**

1. **Öffentlichkeit ist ein Organ**, kein abgeschwächter Operator-Client.  
2. **Mythos · Grund · Beweis** gelten auch für die Website — in getrennten Registern.  
3. **Maximale Sichtbarkeit der Grenze** (disabled HUD, Banner, Geltungsmarken) ist Teil der Heroik, nicht ihr Gegenteil.  
4. Was nicht bewiesen oder nicht public-safe ist, wird **nicht** als Runtime verkauft.  
5. Der Stub **erweitert** V3.3 additiv; er ersetzt weder Kompendium noch Dissertation-as-OS.  
6. **Geltung:** CSP und „keine Funktion“ sind **Satz** der veröffentlichten Fläche; Canvas-Graphen sind **Modell**.

---

## Bogen 1 — Der Ruf

### Herleitung aus dem Nichts

Ein *Stub* ist hier nicht „unfertiges UI“, sondern eine **bewusste öffentliche Form**: Sie beantwortet den Ruf nach Orientierung, ohne den Ruf nach Zugriff zu erfüllen.

### Spezifikation

- URL-Pfad: `/ui-stub/`  
- Kein Build-Schritt; statische Dateien; GitHub Pages.  
- Keine Drittanbieter-Requests (Fonts lokal, Orbitron OFL).

### Heroischer Exkurs

Der Ruf klingt wie ein Lagerfeuer am Rand des Netzes: sichtbar, warm, aber die Schwelle zum Labor bleibt unbetreten.

**Geltung:** Definition des Stub-Begriffs · Satz der Auslieferungspfade im Repo.

---

## Bogen 2 — Die Schwelle

### Spezifikation

| Diesseits (public) | Jenseits (operator-lokal, nicht auf github.io) |
|--------------------|--------------------------------------------------|
| UI-Stub, Landing, Seals, README | Dashboard `:8000`, GraphAPI LIVE, Inject Host, Vault |
| `connect-src 'none'` | `fetch` zu localhost / Mesh |
| Illustrationsgraph | `GET /api/visuals/live-graph` |

### Heroischer Exkurs

Die Schwelle ist die **würdigste** Stelle der Architektur: hier trennt sich, was die Welt sehen darf, von dem, was nur unter Consent und Capability lebt.

**Geltung:** Satz der Policy-Tabelle · Bedingt: Operator-Flächen existieren nur im Plattform-Repo/Runtime.

---

## Bogen 3 — Die Prüfungen

### Spezifikation — Prüfungen, die der Stub bestehen muss

1. **CSP:** `default-src 'self'`; `connect-src 'none'`; kein `form-action` zu Fremden.  
2. **Kein Secret, kein Token, kein Vault-Pfad** im HTML/JS.  
3. **HUD disabled** — Buttons und Selects mit `disabled` + `aria-disabled`.  
4. **Geltungsmarken** sichtbar (Satz / Modell / Fragment).  
5. **Ohne JS** bleibt Banner + Text lesbar; Canvas ist progressive enhancement.  
6. **Kein geschütztes Bildmaterial** (Meister-Hasch nur Seal/Link).

### Beweis-Register (was hier *Satz* ist)

| Aussage | Marke | Nachweis |
|---------|-------|----------|
| Seite lädt ohne Drittanbieter-Hosts | **Satz** | HTML/CSS/JS same-origin; CSP meta |
| Kein Netzwerk aus Stub-JS | **Satz** | `stub.js` ohne `fetch`/`WebSocket` |
| Graph ist nicht Live-GraphAPI | **Satz** | fester `NODES`/`EDGES`-Array |
| „Load-All“ tut nichts | **Satz** | `disabled` Controls |
| Formalpanel als Mathematik-Beweis des OS | **Modell** | Lehrfigur λ, A∈ℝⁿˣⁿ |
| Ästhetik = Campfire-Identität | **Modell** | Design-Tokens, nicht Authentizität des Operators |

**Geltung:** Prüfungen 1–6 = Spezifikation · Tabelle = Beweis-Register mit ehrlichen Grenzen.

---

## Bogen 4 — Der Abgrund

### Was bewusst *fehlt* (Abgrund der Nicht-Darstellung)

- Private Vault-Shards und echte Credentials  
- Offensive Operator-Narrative als „Realraum“  
- Live-Inject in fremde Prozesse  
- GraphAPI mit `FUSION_GRAPH_LIVE` auf der öffentlichen Domain  
- Jede Suggestion, der Stub sei das Dashboard

### Heroischer Exkurs

Der Abgrund ist leer — und diese Leere ist **Schutz**. Wer sie mit falscher Funktion füllt, bricht den Seal der Öffentlichkeit.

**Geltung:** Fragment der Versuchung · Satz der Verbote in Policy/README.

---

## Bogen 5 — Die Wandlung

### Spezifikation — Duales Register (komplexe Form der Oberfläche)

| Register | Organ-Nähe | Stub-Umsetzung |
|----------|------------|----------------|
| **Heroisch** | Mythos | dunkler Canvas, Pulse, Campfire-Glow, Layer-Pips |
| **Formal** | Beweis (Lehrfigur) | helles Raster, G=(V,E), dₙ=d₀·λⁿ, Adjazenz-Hinweis |
| **Grund** | Policy-Banner | public-safe, Geltungsmarken, disabled HUD |

Die **Wandlung** besteht darin, dass dieselbe synthetische Knotenmenge in zwei Prosa-Registern lesbar wird, ohne die Geltung zu vermischen.

### Einschübe (V3.3 Register trennen)

- **Spezifikation:** Dateipfade, CSP, disabled API.  
- **Heroischer Exkurs:** „zwei Register · ein Graph“.  
- **Herleitung aus dem Nichts:** Stub ≠ unfertiges Produkt, sondern public-safe Form.

**Geltung:** Layout/Register = Modell der Didaktik · CSP = Satz.

---

## Bogen 6 — Die Rückkehr

### Spezifikation — Rückkehrwege

| Ziel | Link |
|------|------|
| Startseite Mesh | https://95guknow.github.io/ |
| Plattform-Repo | https://github.com/95guknow/fusion-hero-os |
| Designvorlage V3.3 | `docs/kompendium/V3.3_DESIGNVORLAGE_VERBINDLICH.md` |
| Release | https://github.com/95guknow/fusion-hero-os/releases/tag/v13.0.0 |
| Public Frame Meister Hasch | `docs/dissertation/MEISTER_HASCH_PUBLIC.md` |

### Heroischer Exkurs

Die Rückkehr trägt Orientierung mit — nicht den Schlüssel zum Labor.

**Geltung:** Satz der Verlinkung im Repo · Bedingt: GitHub Pages Deployment des `web/95guknow.github.io/`-Trees (oder Mirror).

---

## Anhang

### A. Dateibaum (Stub)

```
web/95guknow.github.io/
  ui-stub/
    index.html      — Semantik, Banner, dual canvas, disabled HUD, sechs Bögen
    css/stub.css    — Komponenten-Layer
    js/stub.js      — Canvas-Illustration only (kein Netzwerk)
```

### B. Begriffe

| Term | Definition (Zweck) |
|------|---------------------|
| **UI-Stub** | Öffentliche, funktionslose Design-/Orientierungsfläche |
| **Labor Frame** | Alles Operatorische bleibt Hypothese/Runtime im privaten Kontext |
| **Public-safe** | Kein Secret, keine Offensive, kein Vault, CSP eng |
| **Illustrationsdaten** | Feste Demo-Knoten, nicht GraphAPI-Snapshot |

### C. Abgleich Designhandbuch (komplexeste Form)

| V3.3-Pflicht | Umsetzung in diesem Dokument / Stub |
|--------------|-------------------------------------|
| Synthese | oben |
| 6 Bögen | Ruf … Rückkehr |
| Anhang | A–D |
| Geltungsmarken | durchgängig |
| Mythos/Grund/Beweis | Organ-Karten + Register-Tabelle |
| Einschübe getrennt | Spezifikation / Exkurs / Herleitung |
| Duktus | ruhige Perioden, ehrliche Grenzen |
| Additive Evolution | v13-Bezug ohne V3.3-Ersatz |

### D. Was der Stub *nicht* ersetzt

- Operatives Dashboard (`:8000`)  
- Live GraphAPI + WebM-Pipeline im Repo (`live_graph_visuals.py`)  
- Kernel-Inject (Assembly/Host)  
- Kompendium-PDF V3.3 Original

---

**Schluss-Satz:** Der öffentliche Stub ist gelungen, wenn ein Besucher **mehr Orientierung** und **weniger falsche Erwartung** hat — und wenn jede zentrale Aussage ihre Geltungsmarke trägt.
