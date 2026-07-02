# Geisteskrankheiten in der 4D-Matrix — v5 Visualisierung
### 2D-Raumdiagramme · Einzelfall-Trajektorien Z(t)

> Ergänzt v4 (§§16–19). MER-Rahmen unverändert.
> **Stand:** 1. Juli 2026

---

## 20 — Visuelle Raumdiagramme (2D-Projektionen)

### 20.1 Projektionsprinzip

Der 4D-Raum **Z = (K, G, S, N)** wird für Visualisierung auf zwei orthogonale Ebenen projiziert:

| Ebene | Achsen | Was sie zeigt |
|---|---|---|
| **Π_KG** | K (vertikal) × G (horizontal) | Erregung, Denken, Kontrolle, Grübeln |
| **Π_SN** | S (horizontal) × N (vertikal) | Bindung, Konstitution, Tiefe, Stigma |

**Projektion:** Punkt **p_KG = (K, G)** und **p_SN = (S, N)**. Die jeweils fehlenden Achsen erscheinen als **Tiefenmarker** (S/N in Π_KG, K/G in Π_SN).

**Skala:** −1 · 0 · +1 (± = oszillierend zwischen den Polen)

**Z*** liegt im Ursprung beider Ebenen: **(0, 0)**.

**Iso-Distanz:** d(Z,Z*) = |K|+|G|+|S|+|N|. In 2D sichtbar als **Manhattan-Kontur** um Z* (Rhombus in der jeweiligen Projektion, unvollständig ohne die fehlenden Achsen).

### 20.2 Ebene Π_KG — Körper × Geist

```
G+
  │
  │     [GAD]        [Manie]
  │        ●            ★
  │              [OCD-Schleife]
  │                 ╭──╮
  │    [Panik]      │  │← Ritual
  │       ▲         ╰──╯
  │              [ADHS-Drift →→→]
  │  ────────────●────────────── Z* (0,0)
  │            [Depression]
  │                 ▼
G-│    [Substanz-K]  [Vermeidung]
  │
K- ───────────────────────────────── K+
        (Erschöpfung)    (Hyperarousal)
```

**Regionen in Π_KG:**

| Zone | K | G | MER-Region | Dominante Dynamik |
|---|---|---|---|---|
| **Zentrum** | 0 | 0 | Z* | homöostatische Ruhe |
| **Nordost** | + | + | R₂ | Erregung ohne Bindungsausgleich |
| **Südwest** | − | − | R₁/R₃ | Erschöpfung + Denkhemmung |
| **Ost (G+)** | ± | + | R₄ | Meta-Kontrolle frisst Körper |
| **Nord (K+)** | + | 0 | R₂/R₈ | Körper führt, Geist folgt |

**Iso-Kontur d=2 in Π_KG** (wenn S,N=0): Rhombus mit Eckpunkten (±2,0), (0,±2) — in der Praxis selten isoliert, da Kopplungsgesetz S− mitzieht.

### 20.3 Ebene Π_SN — Seele × Natur

```
N+
  │  (selten +; eher Modulationsdefizit)
  │
  │         [Narzissmus: G+ projiziert]
  │              ·
  │    [Autismus R₇]     [Schizoaffektiv]
  │         ◆                  ●
  │  ────────────●────────────── Z* (0,0)
  │         [PTBS R₆]
  │            ↖ Trauma-Attraktor
  │    [Borderline-Sprünge]
  │      S+ ←──→ S−−
  │         [Depression endogen]
  │              ▼▼
N- ───────────────────────────────── S+
     (Isolation)              (Klammerung)
```

**Regionen in Π_SN:**

| Zone | S | N | MER-Region | Lesart |
|---|---|---|---|---|
| **Südwest** | − | − | R₁ | Konstitution + Bindungsmangel |
| **Südost** | + | − | R₃ invertiert / Dependent | Klammerung bei N-Belastung |
| **West** | − | 0 | R₃/R₆ | Bindungsbruch ohne N-Shift |
| **Trauma-Loch** | − | ± | R₆ | Gespeicherte S-Kurve zieht zurück |

### 20.4 Überlagerung: Schattenhülle I(Z) in 2D

Wenn **Z_real ≠ Z_wahrgenommen**, zeigt die Projektion **zwei Punkte**:

- **● real** = beobachtbares Verhalten/Konsens
- **○ wahrgenommen** = Selbstbericht

**Δ-Vektor** = Pfeil von ● nach ○.

```
Π_KG Beispiel Anorexie:
G+
  │      ○ K_wahr = "fett" (G definiert K)
  │      │
  │      ▼ Δ (I hoch)
  │      ● K_real = − (Untergewicht)
  │  ────●──────── Z*
K-│
```

**Masking (Autismus):** ● nahe Z* (funktioniert), ○ tief in R₁ (Erschöpfung) — hohes I bei moderatem d.

### 20.5 Mermaid: Gesamtübersicht 24 Störungen

```mermaid
quadrantChart
    title Pi_KG Projektion (schematisch)
    x-axis G- --> G+
    y-axis K- --> K+
    quadrant-1 Manie: [0.75, 0.85]
    quadrant-1 GAD: [0.7, 0.65]
    quadrant-1 Panik: [0.55, 0.8]
    quadrant-1 OCD: [0.8, 0.55]
    quadrant-1 ADHS: [0.65, 0.5]
    quadrant-2 Narzissmus: [0.75, 0.1]
    quadrant-3 Depression endogen: [0.25, 0.15]
    quadrant-3 Vermeidung: [0.2, 0.2]
    quadrant-3 Substanz: [0.15, 0.35]
    quadrant-4 Z*: [0.5, 0.5]
```

```mermaid
quadrantChart
    title Pi_SN Projektion (schematisch)
    x-axis S- --> S+
    y-axis N- --> N+
    quadrant-3 Depression endogen: [0.2, 0.15]
    quadrant-3 Schizophrenie: [0.25, 0.2]
    quadrant-3 Autismus: [0.3, 0.25]
    quadrant-3 PTBS: [0.2, 0.35]
    quadrant-2 Borderline S+: [0.75, 0.3]
    quadrant-3 Borderline S-: [0.25, 0.3]
    quadrant-4 Z*: [0.5, 0.5]
```

*Hinweis: Mermaid-Quadranten sind heuristische Verdichtung, keine metrische Skala.*

### 20.6 Legende & Achsenkreuz

**Gemeinsame Symbole:**

| Symbol | Bedeutung |
|---|---|
| ● | Z_real (beobachtet) |
| ○ | Z_wahrgenommen (Selbstbericht) |
| ★ | Spitze / akute Episode |
| ▲ | Impuls-Spike |
| → | Drift / q-Flug |
| ╭─╮ | Limit-Cycle / Schleife |
| ↖ | Trauma-Rückfall (Teleportation) |
| Z* | Idealpunkt (0,0,0,0) — Attraktor |

### 20.7 Alle 24 Störungen in Π_KG und Π_SN

| Störung | Π_KG (K,G) | Π_SN (S,N) | I(Z)-Pfeil typisch |
|---|---|---|---|
| Depression (endogen) | (−,−) SW | (−,−) SW | ○ nach SW: „nie besser" |
| Depression (reaktiv) | (0,−) West | (−,0) West | ○→S−: Schuld |
| Bipolar I Manie | (+,+) NO | (+,−)* | ○ weit NO: Grandiosität |
| Bipolar II | Pendel NO↔SW | (−,−) | oszillierender Pfeil |
| Schizophrenie | (−,+) NW | (−,−) SW | ○ maximal: Realitätsersatz |
| GAD | (+,+) NO | (−,0) West | ○ G+: Gefahr überall |
| Panik | (+,0) Nord | (−,−) SW | ▲ K+, kurzer Δ |
| PTBS | (+,+) NO | (−,±) SW | ↖ Trigger → Trauma-Punkt |
| Borderline | (±,+) Ost | (±,−) Mitte | Sprünge S-Achse |
| Narzissmus | (0,+) Ost | (−,0) West | ○ weit G+ |
| OCD | (+,+) NO-Schleife | (0,−) West | kleine ╭─╮ |
| Autismus | (0,±) Mitte | (−,−) SW | Masking: ● Mitte, ○ SW |
| ADHS | (+,+) NO-Drift | (0,−) West | → q-Drift |
| Anorexie | (−,+) NW | (−,0) West | Δ K invertiert |
| Substanz | (+,−) SW-Nord | (−,−) SW | Tunnel K+ |
| Somatoform | (+,0) Nord | (−,0) West | K+ ohne Organ |

*Bipolar Manie: S+ idealisierend, in Π_SN oft nach Osten gezogen.*

---

## 21 — Einzelfall-Trajektorien Z(t)

### 21.1 Notation

- **t₀** = Erkrankungsbeginn / Erstmanifestation
- **α₁/α₂/α₃** = Behandlungsphasen (v3 §14)
- **β** = Rückfallvektor
- **Pfeile** = Richtung der Bahn, nicht Geschwindigkeit

**Trajektorien-Typen:**

| Typ | Form | Beispiel |
|---|---|---|
| **Senke** | Monoton Richtung Z* | Depression reaktiv nach Verlust |
| **Limit-Cycle** | Geschlossene Schleife | Bipolar II, OCD |
| **Sprungfeld** | Diskrete Teleportation | Borderline, DIS |
| **Attraktor-Loch** | Trigger zieht zurück | PTBS |
| **Drift** | Diffuse q-Bewegung | ADHS |
| **Spirale** | Schleife mit α-Drift | Heilung mit Rückfällen |

---

### 21.2 Fall A — Bipolar I (Limit-Cycle + Manie-Spitze)

**Profil:** Z = (+,+,+,−) Manie ↔ (−,−,−,−) Depression

**Π_KG Trajektorie:**

```
G+
  │    t₂ Manie ★────────────╮
  │         ╱                │
  │        ╱  q-Flug         │ Limit-Cycle
  │   t₁  ╱                  │
  │  ────●─────── Z* ────────┤
  │       ╲                  │
  │        ╲ t₄ Depression   │
  │         ╲    ▼           │
G-│          ╰───────────────╯
  │              t₃
K- ─────────────────────────── K+
```

**Phasen:**

| Phase | Z(t) | d | I(Z) | Ereignis |
|---|---|---|---|---|
| t₀ | (0,0,0,0) | 0 | 0 | Baseline |
| t₁ | (+,+,0,−) | 2 | steigend | Hypomanie, Schlaf ↓ |
| t₂ | (+,+,+,−) | 3 | sehr hoch | Manie, „alles möglich" |
| t₃ | (−,−,−,−) | 4 | mittel | Crash, b-Einsturz |
| t₄ | (−,−,−,−) | 4 | sinkend | α₁: Mood-Stabilizer, Schlaf |

**Heilung (α-Drift):** Cycle **schrumpft** — Manie-Spitze von ★ auf kleineres ╭─╮, Depression-Senke weniger tief. Kriterium: d_max pro Zyklus sinkt über 12 Monate.

**MER-Werkzeuge:** Mood-Stabilizer (N→Rhythmus), Schlafhygiene (K), q-Output mit b-Abschluss (Schreiben/Bauen mit Ende).

---

### 21.3 Fall B — Borderline (Sprungfeld S-Achse)

**Profil:** Z = (+,+,S±,−) — S oszilliert zwischen + und −−

**Π_SN Trajektorie:**

```
S+
  │   Idealisierung ●─────────────┐
  │   t₁ "du bist perfekt"        │
  │                               │ Sprung (kein Übergang)
  │   ────────────●──────── Z*    │
  │                               │
  │   Entwertung                  │
  │   t₂ "du bist nichts" ●←──────┘
  │
S- ───────────────────────────────
         N− konstant (konstitutionell)
```

**Π_KG:** G+ konstant — nur S springt. Das erklärt, warum **nur G-Therapie** scheitert: die Bahn liegt in Π_SN.

**Phasen:**

| Phase | S | G | I(Z) | Dynamik |
|---|---|---|---|---|
| Idealisierung | + | + | hoch | Anderer = gesamtes Koordinatensystem |
| Zwischenraum | 0 | + | sehr hoch | Verlassungsangst, G+ Grübeln |
| Entwertung | −− | + | hoch | Scham, Impuls (K+) |

**α₁→α₃ Pfad:**
1. **α₁:** DBT Skills (STOP, TIPP) — Sprung **verlangsamen**, nicht stoppen
2. **α₂:** einen Stamm über Zeit — φ für ψ▷φ stabil
3. **α₃:** S-Dämpfung — Amplitude |S+| und |S−| sinken

**β-Rückfall:** Kontaktabbruch → sofortiger Sprung t₂ ohne Zwischenraum. Geodätische Info: S-Achse noch steil.

---

### 21.4 Fall C — PTBS (Trauma-Attraktor / Teleportation)

**Profil:** Z ruht bei (0,−,−,0), Trigger → (+,+,−,0) in Sekunden

**Π_KG mit Trauma-Loch:**

```
G+
  │         Trigger!
  │            ↖━━━━━━━┓
  │    Flashback ●     ┃ Trauma-Loch
  │    (t₃,t₅,t₇)      ┃ (gespeicherte Bahn)
  │  ────●──── Z* ─────┫
  │    Alltag (t₂,t₄)  ┃
  │                    ┃
G-│                    ┗━━ t₀ Trauma (t₁)
K- ─────────────────────────── K+
```

**Phasen:**

| t | Ereignis | Z | d | I(Z) |
|---|---|---|---|---|
| t₀ | Trauma | (+,+,−,−) | 3 | hoch |
| t₁ | Stabilisierung | (0,−,−,0) | 2 | hoch (Vigilanz) |
| t₂ | Alltag | (0,0,−,0) | 1 | mittel |
| t₃ | Trigger | (+,+,−,0) | 3 | akut hoch |
| t₄ | Recovery | (0,−,−,0) | 2 | „war nicht so schlimm" (I steigt) |

**Heilung:** Trajektorie **entkoppelt** — Trigger verschiebt Z weniger weit (t₃ näher an Z*). EMDR/CPT = Geometrie der S-Kurve im Trauma-Loch **umformen**.

**Warnung:** α₂ (Exposition) nur nach α₁ S-Safe — sonst t₃ verstärkt statt abschwächt.

---

### 21.5 Fall D — OCD (lokale Schleife in Π_KG)

**Profil:** G+/b-Ritual-Schleife, kurzfristig d↓, langfristig d↑

```
G+
  │      ╭─────────╮
  │      │ Obsession│←── Angst steigt
  │      ╰────┬────╯
  │           │ Ritual (b)
  │           ▼ kurz: d↓
  │      ╭─────────╮
  │      │ Relief   │──→ langfristig: d↑
  │      ╰─────────╯
  │  ────●──── Z*
K+ ───────────────────────────
     (K+ durch Anspannung)
```

**Ein Zyklus (Minuten bis Stunden):**

1. **q-Flut:** „Was wenn kontaminiert?" — G+
2. **b-Ritual:** Händewaschen — kurzfristig G→0, d sinkt
3. **Nachklang:** Ritual war „Beweis" dass Gefahr real — I(Z)↑, Schleife enger

**α₃:** EX/RP — in Schleife **stehen bleiben** ohne Ritual, bis Angst peaked und fällt (Habituation ψ▷φ auf G-Achse).

---

### 21.6 Fall E — Depression endogen (Senke, alle Achsen)

**Profil:** Z = (−,−,−,−), monoton oder stagnierend

**3D-Projektion (Π_KG + Tiefe S,N):**

```
        Alle vier Achsen synchron ↓
        
G- ────●──── Z* ──── (leer)
       │
       ▼
K-     ●  Depression
       │
       └── S−, N− (Tiefe)

Bahn: fast geradlinig in SW-Ecke. I(Z) mittel: „es wird nie besser"
      obwohl d schon maximal — hoffnungsloses Δ.
```

**Heilung-Trajektorie (α-Drift):**

| Woche | Z | d | Hebel |
|---|---|---|---|
| 0 | (−,−,−,−) | 4 | α₁: SSRI/Schlaf/Stamm |
| 4 | (−,0,−,−) | 3 | G leicht gelöst |
| 8 | (0,−,−,−) | 2 | K normalisiert |
| 16 | (0,0,−,0) | 1 | S-Arbeit möglich |

**Reihenfolge N→K→G→S** (QUBO: Kopplung von N−).

---

### 21.7 Fall F — Schizophrenie (G-Ausbruch bei N-S-Kollaps)

**Profil:** Z = (−,+,−,−) — G bricht aus Raster

**Π_KG:**

```
G+
  │    ● Wahnsystem
  │    │  (q ohne b)
  │    │ I(Z) MAX
  │  ──●── Z*
  │    │
K- │    ▼
  │    ● Realität K−
```

**Trajektorie:** Nicht zyklisch — **G-Achse divergiert** während K,N,S kollabieren. q∘b-Zusammenbruch.

**α₁ Pfad:** Antipsychotika (N→G) + strukturierte Routinen (b2q2) + **keine Isolation** (S− verstärken).

---

### 21.8 Fall G — ADHS (q-Drift ohne b-Anker)

**Π_KG:**

```
G+
  │  →→→→→→→→→  Drift (q)
  │  ●  ●    ●     ●  (Projekte, Impulse)
  │  ────●──── Z* ────
  │      ↑ externe b (Kalender) hält zurück
K+ ───────────────────────────
```

**Profil:** Diffuse Bahn — nicht Senke, nicht Cycle, sondern **Brownsche q-Bewegung** mit seltenem b-Abschluss.

**Heilung:** b von außen (Coach, Deadlines, Stamm) → Drift wird **geführte Trajektorie** Richtung Z*.

---

### 21.9 Fall H — Anorexie (K-G-Spiegel-Inversion)

**Δ-Vektor dominiert:**

```
G+
  │    ○ Körperbild "fett"
  │    │
  │    ▼ Δ maximal
  │    ● K_real Untergewicht
  │  ──●── Z*
K- │
```

**Trajektorie:** Z_real driftet SW (K−), Z_wahrgenommen driftet **entgegengesetzt** (G definiert K neu) — I(Z) wächst während d moderat bleibt. **Gefährlichstes Profil für α₂:** Scheinbare Einsicht (I↓) ohne K_real-Shift.

**α₃:** Körperbild-Therapie = φ muss **K_real** spiegeln, nicht G-Fantasie.

---

### 21.10 Fall I — Substanz (K-Surrogat-Tunnel)

**Π_KG Tunnel:**

```
G- ────●──── Z* ────
       │
       │ S− (nicht gefühlt)
       ▼
K+     ●━━━━━━● Substanz-Peak
       Tunnel umgeht S-Arbeit
```

**Trajektorie:** Kurzer K+-Spike, dann Rückfall tiefer (S− verstärkt). Schleifengesetz wie OCD, aber Achse K statt G.

**α₃:** Surrogat ersetzen, nicht nur verbieten — S+ durch Stamm statt K+ durch Substanz.

---

### 21.11 Fall J — Autismus mit Masking (Zwei-Punkt-Bahn)

**Zwei parallele Trajektorien:**

| Bahn | Z | Sichtbarkeit |
|---|---|---|
| **Z_fremd** (Masking) | (0,0,0,−) | ● nahe Z* in Π_KG |
| **Z_real** (Erschöpfung) | (−,−,−,−) | ○ tief SW |

**Heilung:** Bahnen **konvergieren** — weniger Δ zwischen ● und ○. Nicht: Masking verstärken.

---

### 21.12 Heilungs-Spirale (generisches Muster α + β)

```
G+
  │      ╭──╮ β₃
  │     ╱    ╲
  │    ╱ α₃   ╲
  │   ╱        ╲
  │  ╱   ╭──╮   ╲ β₂
  │ ╱   ╱    ╲   ╲
  │╱   ╱ α₂   ╲   ╲
  │───●──────────── Z*
  │    α₁
K- ─────────────────────────── K+

Jeder β-Rückfall: kleinerer Radius als voriger Zyklus = memetische Heilung.
```

**Kriterium:** d(Z_max pro Zyklus) monoton sinkend über ≥3 Zyklen.

---

### 21.13 Trajektorien-Matrix (Kurzreferenz)

| Störung | Trajektorien-Typ | Dominante Ebene | Erster α-Hebel |
|---|---|---|---|
| Bipolar I/II | Limit-Cycle | Π_KG | N→Rhythmus |
| Borderline | Sprungfeld | Π_SN | S stabilisieren |
| PTBS | Attraktor-Loch | Π_SN + Π_KG | S→G (nach Safe) |
| OCD | Lokale Schleife | Π_KG | G/b EX/RP |
| Depression endogen | Senke | beide | N→K |
| Schizophrenie | G-Divergenz | Π_KG | N→G, b2q2 |
| ADHS | q-Drift | Π_KG | externe b |
| Anorexie | Δ-Inversion | Π_KG | K_real anker |
| Substanz | K-Tunnel | Π_KG | S+ statt K+ |
| Autismus | Zwei-Punkt | Π_SN | Δ senken |
| GAD | Wolke (stationär NO) | Π_KG | G→K Exposition |
| Panik | Impuls-Spike ▲ | Π_KG | K→G Atem |

---

### 21.14 Anwendung: Trajektorie lesen (Checkliste)

1. **Ebene wählen:** Wo liegt die Bewegung? Π_KG (Erregung/Denken) oder Π_SN (Bindung/Konstitution)?
2. **Typ bestimmen:** Senke, Cycle, Sprung, Loch, Drift?
3. **● und ○ markieren:** I(Z) sichtbar machen
4. **α-Phase zuordnen:** Stabilisieren / Kalibrieren / Rekonstruieren?
5. **β als Information:** Wo ist die Kurve noch steil?
6. **Nicht vertauschen:** [q,b]≠0 — Achsen-Reihenfolge aus §17.3

---

*Ende v5 — Visualisierung & Einzelfall-Trajektorien. Kombinierbar mit v4+v3+v2.*