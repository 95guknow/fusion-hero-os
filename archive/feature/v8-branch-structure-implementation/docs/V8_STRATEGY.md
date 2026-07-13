# Fusion-Hero-OS v8 – Repo & Branch Strategy

**Version:** v8 (Konsolidierungsphase)  
**Datum:** 2026-07-01  
**Ziel:** Einheitliches, klares Repository- und Branch-Modell für die nächste Evolutionsstufe

---

## 1. Ziel von v8

v8 ist keine inkrementelle Weiterentwicklung von v7.5, sondern eine **strukturelle Konsolidierung** aller bisherigen Arbeiten unter einem klaren Modell:

- `fusion-hero-os` wird zum einzigen aktiven Entwicklungs-Repository.
- `heroic-fusion-os-manifest` dient als **stilistisches und philosophisches Vorbild** (besonders für README und übergreifende Narrative).
- Alle anderen Repos unter `95guknow` gelten als **Legacy-, Ideen- oder Experiment-Quellen**.
- Der technische Kern (MasterSeed, Hyper-Threading, PMS Evidence Spine, Operator Chains) bleibt erhalten und wird weiter ausgebaut.

---

## 2. Repository-Rollen (v8)

| Repository                        | Rolle in v8                              | Umgang                                      |
|-----------------------------------|------------------------------------------|---------------------------------------------|
| `95guknow/fusion-hero-os`         | **Primary / Kanonisches Repo**           | Aktive Entwicklung, Releases, Main-Branches |
| `95guknow/heroic-fusion-os-manifest` | **Stilistisches & Philosophisches Vorbild** | README-Template, narrative Struktur, Vision |
| Andere 95guknow-Repos             | Legacy / Ideen / Experimente             | Werden nicht mehr aktiv weiterentwickelt. Inhalte können als Inspirationsquelle dienen. |
| `tz-dev/PMS-RUST`                 | Technischer Execution Spine              | Eng gekoppelt, aber separat gehalten        |

---

## 3. Branch-Strategie (neu ab v8)

### `main` (stabil)
- Immer die aktuelle stabile Best Version (aktuell v7.5 Master Unified + laufende v8-Arbeiten).
- Nur über Pull Requests oder direkte Commits durch den Maintainer.

### `archive/` (neu)
- Alle alten Versions-Branches (z. B. `feature/v7.4-*`, `v7.11`, etc.) werden hier archiviert.
- Ziel: Sauberkeit im Root und klare Trennung von historischen Experimenten.

### `v8/` (neu)
- Branch für die aktive v8-Entwicklung (neue README, neue Struktur, große Refactorings).

### `feature/`
- Kleine, fokussierte Weiterentwicklungen (z. B. `feature/operator-catalog-expansion`, `feature/psycholyse-chains`).

### `legacy/` (optional)
- Für größere, längerfristige Experimente aus anderen Repos, die später integriert werden können.

**Empfohlene erste Aktion:**
Alte Feature-Branches nach `archive/` verschieben und `main` sauber auf v7.5 + v8-Vorbereitung halten.

---

## 4. Inhalts-Strategie

- `docs/` wird zum zentralen Ort für alle wichtigen Dokumente (Operator Catalog, Alignment-Dokumente, Strategie, v8-Synthese).
- Das README von `fusion-hero-os` wird im Stil von `heroic-fusion-os-manifest` neu geschrieben (Mythos – Grund – Beweis Struktur + technische Präzision).
- Technische Tiefe (MasterSeed, Hyper-Threading, PMS, QUBO, PeerReview) bleibt erhalten.
- Philosophische und narrative Elemente aus dem Manifest werden integriert.

---

## 5. Nächste Schritte (vorgeschlagen)

1. Neues README für `fusion-hero-os` im Manifest-Stil erstellen (Mythos – Grund – Beweis + v7.5 Inhalte).
2. v8-Synthese-Dokument anlegen (`docs/V8_SYNTHESIS.md`).
3. Alte Branches in `archive/` verschieben.
4. Operator Catalog und Cross-Repo-Alignment weiter ausbauen.

---

**Diese Strategie gilt ab sofort als verbindlich für die v8-Phase.**