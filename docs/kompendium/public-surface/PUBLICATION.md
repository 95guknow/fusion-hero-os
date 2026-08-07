# Publication — Public Surface Only Kompendium v1.0.0

**Author (Klarname):** Stephan Hagen Urban  
**Operator-Handle:** `=====stephanhagenurban` · `=====stephanhagenurban1`  
**Title (DE):** Public Surface Only. Kein Vault · Kein Seal · Nur öffentliche Surface  
**Title (EN):** Public Surface Only. No Vault · No Seal · Public Surface Alone  
**Subtitle:** Ein additivs Kompendium der Heroik (V3.3) im Fusion Hero OS — Siegfried-Moment, Nibelungen, Grimm-Katalog, BIG ALPHA  
**Field:** Autopoietische Autopolitik / Public Ethics / Software-Architektur (Geltungstrennung)  
**Platform:** Fusion Hero OS VERSION **15.2.0**  
**Design:** Kompendium der Heroik V3.3 (Synthese + 6 Bögen + Anhang)  
**Tag (vorgeschlagen):** `public-surface-only-v1.0.0`  
**Published (local package):** 2026-08-07  
**Repo:** https://github.com/95guknow/fusion-hero-os  
**Public mesh:** https://95guknow.github.io  

---

## Vocabulary (Repo)

| Verb | Bedeutung |
|------|-----------|
| **deploy** | private / operator host |
| **push** | public (GitHub) |
| **merge** | both via dual timeline + Human-Confirm-Gate |

Dieses Paket ist **publication-ready lokal**. Öffentlicher Release (push/tag) erfordert Operator-Freigabe.

---

## Fixpunkt (EXAKT)

> **Kein Vault. Kein Seal. Nur öffentliche Surface.**  
> Public Surface = Expression ohne Vault-Commit und ohne Seal-Theater.

---

## Files (Buch-Paket)

| Datei | Rolle |
|-------|--------|
| `Public_Surface_Only_Kompendium_v1.0.0.pdf` | **Hauptwerk (Buch-PDF)** |
| `Public_Surface_Only_Kompendium_v1.0.0.md` | Kurz-Index / Begleit-MD |
| `_build_public_surface_kompendium_pdf.py` | Reproduzierbarer Build |
| `PUBLICATION.md` | dieses Record |
| `ACADEMIA_UPLOAD_PASTE.txt` | Copy-Paste Academia / Zenodo / Website |
| `RELEASE_NOTES_v1.0.0.md` | GitHub Release-Text |

### Kanon-Quellen (Mythos-Schicht)

- `docs/mythos/PUBLIC_SURFACE_ONLY.md`
- `docs/mythos/SIEGFRIED_MOMENT.md`
- `docs/mythos/NIBELUNGEN_SAGA.md`
- `docs/mythos/GRIMM_MAERCHEN_VOLLAUSGABE.md`
- `docs/mythos/BIG_ALPHA_SIEGFRIED_ASSET_LEDGER.md`
- `docs/mythos/KHM_INDEX.yaml`

---

## Impressum / Attribution (public-safe)

| Feld | Wert |
|------|------|
| Autor | Stephan Hagen Urban |
| Handle | 95guknow · =====stephanhagenurban |
| Organisation | Senfkorn UG (Holding & Operations / WIR Mesh) |
| Lizenz-Hinweis | Labor / public-safe Expression; Vault und Secrets **nicht** Teil dieser Publikation |
| Kontakt-Surface | https://95guknow.github.io · https://github.com/95guknow |

**Business-Trennung:** siehe `business/STEPHAN_HAGEN_URBAN_BUSINESS_PERSONA_PUBLICATION.md` — private Feldtests nicht in Business-Kanäle.

---

## Release-Schritte (Operator)

### A) Lokal (erledigt)

1. PDF gebaut und verifiziert (4 Seiten, V3.3-Bögen)
2. Publication record + Academia-Paste + Release notes

### B) GitHub (nach Human-Confirm)

```powershell
cd C:\Users\Admin\fusion-hero-os
# nur mythos + kompendium public-surface + modul + registry (fokussierter Commit)
git add docs/mythos docs/kompendium/public-surface docs/kompendium/README.md `
  fusion_hero_os/core/nibelungen_mythos.py fusion_hero_os/registry.py `
  artifacts/2026-08-07_*.md
git status
git commit -m "publish: Public Surface Only Kompendium v1.0.0 (=====stephanhagenurban)"
# PR / push — Human-Confirm-Gate beachten
git tag -a public-surface-only-v1.0.0 -m "Public Surface Only Kompendium v1.0.0 — Stephan Hagen Urban"
# git push origin HEAD && git push origin public-surface-only-v1.0.0
```

Release-URL (nach Push):  
https://github.com/95guknow/fusion-hero-os/releases/tag/public-surface-only-v1.0.0

### C) Academia.edu

1. https://independent.academia.edu/StephanUrban1 → Upload  
2. Title / Abstract: `ACADEMIA_UPLOAD_PASTE.txt`  
3. Author: **Stephan Hagen Urban**  
4. Attach: `Public_Surface_Only_Kompendium_v1.0.0.pdf`

### D) Optional Surfaces

- Zenodo DOI (community upload)  
- 95guknow.github.io — Download-Link zum PDF  
- Instagram pack: **NO TARNKAPPE · PUBLIC** tile (separates Asset) + Buch-Hinweis

---

## Honesty

- Dieses Werk ist **kein** juristischer Verlagstitel mit ISBN (sofern nicht separat beantragt).  
- Es ist **Kompendium-Expression** im Dissertation-as-OS-Frame.  
- Saga/Märchen-Anteile = **Modell**, nicht mathematischer Satz.  
- Kein Vault-Inhalt in diesem Buch.

**Status:** **LOKAL VERÖFFENTLICHUNGSFERTIG** · GitHub/Academia: warte auf Operator-Push-Freigabe.
