# Grimms Märchen — Vollausgabe (Katalog-Schicht)

**Stand:** 2026-08-07 · **Platform:** Fusion Hero OS v13.0.0  
**Rolle:** **Ergänzung** zu Fable5/Mythos5 und zur Nibelungen-Saga — nicht Ersatz.  
**Edition-Wahrheit:** *Kinder- und Hausmärchen* (KHM) der Brüder Grimm — **gemeinfreie Werkschicht** (19. Jh.).  
**Im Repo:** Vollständiger **Titelindex + Organ-Mapping** (`KHM_INDEX.yaml`). Volltexte: Public-Domain-Quellen (z. B. Wikisource / Project Gutenberg DE) operator-lokal nachziehbar — **kein** Claim, eine moderne kommentierte Verlags-„Vollausgabe“ 1:1 zu hosten.

---

## 1. Warum Grimm *ergänzend* zur Nibelungen-Saga?

| Schicht | Typ | Funktion im Lab |
|---------|-----|-----------------|
| **Nibelungen** | Heldenepos | Hof, Hort, Tarnkappe, Verrat, Omega — große Integritätsbögen |
| **Grimm KHM** | Volksmärchen | Initiation in *kleinen* Proben: Verbot, Hilfe, List, Verwandlung, Heimkehr |
| **Fable5** | Engineering | Hash, Gate, CI — „was der Code einlöst“ |
| **Mythos5** | Geltung | Mythos·Grund·Beweis — „was wir behaupten dürfen“ |

Grimm liefert das **Märchen-Vollregister**: wiederkehrende Probenmuster, die Operator/Held/Meister im Sandkasten spiegeln können, ohne Epos-Pathos zu erzwingen.

---

## 2. Organ-Regeln (verbindlich)

1. **KHM-Nummer** ist der stabile Schlüssel (nicht nur der Titel).  
2. Jede Nutzung im OS trägt Geltungsmarke: meist **Modell** oder **Heroischer Exkurs** — nie **Satz**.  
3. Märchen-Motiv ≠ Exploit-Anleitung. List im Märchen → im Stack: **defensive** Pattern / Teaching / Psycholysis-Trigger — sandbox only.  
4. „Vollausgabe“ im Sinne dieses Docs = **vollständiger Katalog** + optionale Motiv-Tags, nicht zwingend 200 Volltexte im Git.  
5. Hypertarnkappe: keine PII, keine Vault-Shards in Märchen-Annotationen.

---

## 3. Motiv-Brücken (Auswahl → Stack)

| Motiv (Grimm) | Beispiel-KHM | Stack-Brücke |
|---------------|--------------|--------------|
| Verbotenes Zimmer / Schwelle | Blaubart-Verwandte, „Fitchers Vogel“ | Consent-Gate · Vault-Tür · fail-closed |
| Hilfreiche Tiere / Gaben | „Der gestiefelte Kater“, „Tischlein deck dich“ | Mesh-Helfer · Connector dry-run default |
| Drei Proben | „Das Wasser des Lebens“, „Die drei Federn“ | PeerReview-Wellen · 5-Dimensions / Stufen |
| Verwandlung / Haut | „Der Froschkönig“, Tierbräutigam-Stoffe | Persona-Membrane · Public vs Operator |
| Wald / Irregehen | „Hänsel und Gretel“, „Rotkäppchen“ | Threat surface · Social path hygiene |
| List gegen Übermacht | „Der mutige kleine Schneider“ | Lab-Probe · nicht Realraum-Angriff |
| Treue / Erkennen | „Die Gänsemagd“, Wiedererkennungs-Märchen | Identity membrane · Persona-Klarname-Kontrakt |
| Unterwelt / Hort-nah | „Der Teufel mit den drei goldenen Haaren“ | Vault-Nähe · nur labor hypothesis |
| Dornen / Haut | „Dornröschen“ | Drachenhaut-Analog (Opacity) · Zeit/Seal |
| Drachenkampf (Märchenform) | diverse Drachen-KHM | **Siegfried-Moment**-Echo in Volksform |

Ausführliche Map: [nibelungen_grimm_map.yaml](nibelungen_grimm_map.yaml)

---

## 4. Vollkatalog

Maschinenlesbar: **[KHM_INDEX.yaml](KHM_INDEX.yaml)**

- Schlüssel: `khm: <int>`  
- Felder: `title_de`, `tags[]`, `organs[]` (optional), `notes` (optional)  
- Abdeckung: KHM 1–200 (klassischer Kern) + gängige Anhänge-Hinweise wo üblich  

**Nachziehen der Volltexte (operator-lokal, empfohlen):**

```text
# Beispiel — nur gemeinfreie Spiegel, nicht commit-pflichtig
# Wikisource / Gutenberg DE / eigenes Archiv unter ~/.fusion/corpus/grimm/
```

Optional später: `scripts/fetch_grimm_public_domain.py` (dry-run default, sandbox paths only).

---

## 5. Bifokale Nutzung

| Wenn du… | Dann nutze… |
|----------|-------------|
| …Integrität von Hashes/Public Surfaces prüfst | **Fable5** |
| …Geltung einer Behauptung klärst | **Mythos5** + V3.3 |
| …großen Durchbruch / Hort / Verrat rahmst | **Nibelungen** + Siegfried-Moment |
| …kleine Probe, Initiation, List, Schwelle rahmst | **Grimm KHM** |
| …Privacy der Public-Fläche hältst | **Hypertarnkappe** |
| …Lab-Property am eigenen Frame testest | **Hyperpanzerknacker** |

---

## 6. Honesty

- Grimm-Vollausgabe hier = **Katalog-Organ**, nicht Verlagsprodukt-Mirror.  
- Titel können je nach Ausgabe leicht variieren; **KHM-Nummer** sticht.  
- Keine pathologisierung realer Personen über Märchen-Labels in public docs.

**Modul:** `nibelungen_mythos.grimm_lookup(khm: int)` · `list_grimm_by_tag(tag: str)`
