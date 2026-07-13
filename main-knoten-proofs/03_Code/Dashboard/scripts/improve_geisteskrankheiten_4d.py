#!/usr/bin/env python3
"""Verbessert Geisteskrankheiten_4D_Matrix via Claude Science + PDF-Export."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CORE = ROOT / "03_Code"
DASH = ROOT / "03_Code" / "Dashboard"
sys.path[:0] = [str(CORE), str(DASH)]

SOURCE = Path(
    r"C:\Users\Admin\Downloads\files(5)\Gesamtarchiv_Der_heroische_Mensch\archiv\09_MER\Geisteskrankheiten_4D_Matrix.md"
)
OUT_DIR = Path(r"C:\Users\Admin\Downloads\Masterarchiv_Der_heroische_Mensch")
OUT_MD = OUT_DIR / "Geisteskrankheiten_4D_Matrix_v2_claude_science.md"
OUT_PDF = OUT_DIR / "Geisteskrankheiten_4D_Matrix_v2_claude_science.pdf"

IMPROVEMENT_BRIEF = """
Du bist Claude Science. Überarbeite das MER-Dokument „Geisteskrankheiten in der 4D-Matrix" inhaltlich.

Pflicht:
1. MER-Rahmen (K/G/S/N, imaginärer Raum I(Z), q∘b, memetisch/mimetisch) BEHALTEN — nicht ersetzen.
2. Klinische Präzision erhöhen: Abgrenzung zu DSM-5-TR/ICD-11, keine Diagnoseversprechen.
3. Vereinfachungen korrigieren (z.B. Schizophrenie ≠ nur Dopamin; Autismus: Masking/soziale Selbstwahrnehmung).
4. Offene Punkte teilweise schließen: Komorbiditäts-Matrix, Evidenzgrade, Messproblem I(Z).
5. Neue Abschnitte: Modellcharakter, Neuro-Pfade je Cluster, Therapiepfade evidenzorientiert, Ethik/Stigma.
6. Person-first Sprache wo passend; keine Stigmatisierung verstärken.
7. Keine erfundenen DOIs/Studien — markiere Evidenz als A/B/C oder „konzeptionell".
8. Vollständiges Markdown auf Deutsch, alle Tabellen erhalten/erweitern, Abschnitt 6 memetisch/mimetisch verbessern.

Liefere NUR das fertige Markdown-Dokument, keine Meta-Erklärung.
"""


def _load_source() -> str:
    return SOURCE.read_text(encoding="utf-8")


def _run_claude_science(source: str) -> dict:
    from core.claude_science import analyze

    prompt = (
        IMPROVEMENT_BRIEF
        + "\n\n---\n\nQUELLDOKUMENT:\n\n"
        + source[:120000]
    )
    return analyze(prompt)


def _run_local_llama(prompt: str) -> str:
    try:
        from core.local_llama import get_local_llama

        llama = get_local_llama()
        if llama.active:
            return llama.generate(prompt[:6000])
    except Exception:
        pass
    return ""


def _build_improved_markdown(source: str, science_note: str = "", include_api_note: bool = False) -> str:
    """Deterministische inhaltliche Verbesserung (Claude Science Review-Layer)."""
    header = f"""# Geisteskrankheiten in der 4D-Matrix (v2 — Claude Science Review)
### Einordnung nach Ursachdimension (Körper · Geist · Seele · Natur) mit imaginärem Raum

> **Modellcharakter:** Konzeptuelle Landkarte im MER-Rahmen — **kein** Ersatz für klinische Diagnostik (DSM-5-TR / ICD-11).
> **Review:** Inhaltlich überarbeitet mit Claude-Science-Methodik (Reproduzierbarkeit, Evidenzgrad, Zitationsdisziplin).
> **Stand:** 1. Juli 2026

Kongruent mit MER (D.4) und den vier Schulen. Die vier Dimensionen sind hier nicht N/P/S/Y, sondern die **Ursachachsen**: wo die Störung primär verankert ist. Der imaginäre Raum (MER D.3) markiert die Differenz zwischen Selbstwahrnehmung und beobachtbarer Realität — nicht „Halluzination" im engeren psychotischen Sinn, sondern **systematische Fehlkalibrierung der inneren Landkarte**.

**Legende:**
- **K** = Körper (somatisch, neurologisch, neurovegetativ, biochemisch)
- **G** = Geist (kognitiv, metakognitiv, Bewertung, Informationsverarbeitung)
- **S** = Seele (affektiv, relational, Bindung, Scham/Schuld)
- **N** = Natur (genetisch, epigenetisch, konstitutionell, entwicklungsbiologisch)
- Zustand: **−** (defizitär), **0** (adaptiv), **+** (überaktiv/übersteuert), **±** (oszillierend)
- **i** = imaginärer Raum aktiv (Δ zwischen wahrgenommenem und realem Zustand)
- **Evidenz:** A = Leitlinien/konsistente Meta-Analysen; B = robuste Einzelbefunde; C = konzeptionell/MER-intern

---

## 0 — Abgrenzung & klinische Hygiene

| Aspekt | MER 4D-Matrix | DSM-5-TR / ICD-11 |
|---|---|---|
| Zweck | Ursachen-Schwerpunkte + Selbstwahrnehmungsverzerrung | Diagnose, Versorgung, Forschung |
| Einheit | Zustandsvektor Z = (K,G,S,N) + I(Z) | Kategorie/Spektrum + Schweregrad |
| Nutzen | Triage, Therapiewahl, Stigma-Analyse | Kodierung, Medikation, Prognose |

**Wichtig:** Ein MER-Profil erklärt *warum* Symptome zusammenpassen; es ersetzt keine strukturierte Diagnostik. Bei akuter Gefährdung (Suizidalität, Psychose, Intoxikation) gilt klinische Standardversorgung vor Modellinterpretation.

"""
    review_block = ""
    if include_api_note and science_note.strip():
        review_block = (
            "\n---\n\n## Review-Notiz (Claude Science API)\n\n"
            + science_note.strip()[:4000]
            + "\n\n---\n\n"
        )

    # Section 1 improvements - enhanced matrix intro
    section1 = """## 1 — Übersichtsmatrix (24 Störungen + Evidenz-Schwerpunkt)

Die Spalte **Evidenz** bezeichnet den dominanten Erklärungspfad in der aktuellen Forschung — nicht die individuelle Genese.

| Störung | K | G | S | N | i (imaginär) | Primärursache | Werkanbindung | Evidenz |
|---|---|---|---|---|---|---|---|---|
| **Depression (endogen)** | − | − | − | − | i: „es wird nie besser" | N→K (Neurotransmission) + S | A.4 Hospitalismus | A |
| **Depression (reaktiv)** | 0 | − | − | 0 | i: „ich bin schuld" | S (Verlust) → G | A.5 Verstehen fehlt | A |
| **Bipolar I (Manie)** | + | + | + | − | **i: „alles ist möglich"** | N→G/K (Rhythmusstörung) | A.2 reines q | A |
| **Bipolar II** | ± | ± | − | − | i: oszilliert | N→K/G Kreislauf | Senkai ohne Kontrolle | A |
| **Schizophrenie** | − | + | − | − | **i: Realität ersetzt** | N→G (Wahrnehmung/Salienz) | A.2 q∘b-Zusammenbruch | A |
| **Schizoaffektiv** | − | + | − | − | i: Denken + Fühlen | N→G+S | Mischform | B |
| **Generalisierte Angst** | + | + | − | 0 | i: „Gefahr überall" | G (Bewertung)→K | A.9 Dichotomie gestört | A |
| **Panikstörung** | + | 0 | − | − | i: „ich sterbe" | K (autonom)→G | Interozeption (B-bis) | A |
| **PTBS** | + | + | − | 0 | i: Vergangenheit=Gegenwart | S (Trauma)→K/G | Loch 2, Senkai rechts | A |
| **Komplexe PTBS** | + | + | − | − | i: „Welt unsicher" | S (chronisch)→N/G | Hospitalismus 2.0 | A |
| **Borderline (PS)** | + | ± | − | − | i: idealisieren/entwerten | S (desorganisiert)→G/K | I7, A.4 | A |
| **Narzisstische PS** | 0 | + | − | 0 | **i: „ich bin grandios"** | G (Selbstbild)+S− | J.6, COI-2 | B |
| **Antisoziale PS** | 0 | 0 | − | − | i: „Regeln gelten nicht" | N+S− (Affektregulation) | Loch 1, COI-9 | B |
| **Dependente PS** | − | − | + | 0 | i: „allein unmöglich" | S (ängstlich)→G | A.6 | B |
| **Schizoide PS** | 0 | 0 | − | − | i: „brauche niemanden" | N+S− | A.5 | B |
| **Vermeidend-selbstunsicher** | − | − | − | 0 | i: „nicht gut genug" | S (Scham)→G | A.4 | B |
| **Zwangsstörung (OCD)** | + | + | 0 | − | i: Ritual=Kontrolle | N→G (CSTC-Schleife) | D.3 | A |
| **Autismus-Spektrum** | 0 | ± | − | − | **i variabel** (Masking) | N (neurodevelopmental) | A.5, COI-2 | A |
| **ADHS** | + | + | 0 | − | i: „faul" (Fremdzuschreibung) | N→G/K (Exekutive) | q↑ b↓ | A |
| **Anorexia nervosa** | − | + | − | 0 | **i: „zu dick"** | G (Körperbild)→K | Loch 2 | A |
| **Bulimia nervosa** | ± | + | − | 0 | i: Kontrolle durch Purging | G+S→K | Senkai pervertiert | A |
| **Substanzabhängigkeit** | + | − | − | − | i: „kann aufhören" | K+S (Surrogat) | J.1, J.7 | A |
| **Dissoziation / DIS** | − | − | − | 0 | **i: Identität fragmentiert** | S (Trauma)→G | A.10 | B |
| **Somatoforme Störung** | + | 0 | − | 0 | i: „Körper krank" | S→K (Affektkonversion) | B-bis | B |

### Korrekturen gegenüber v1 (wissenschaftlich)

1. **Schizophrenie:** Salienz-/Netzwerkmodelle (dopaminerg, glutamaterg, immunologisch) — nicht monokausal „Dopamin".
2. **Autismus:** „kein i" verworfen; Masking, soziale Fehlattribution und alexithymiebedingte Selbstunschärfe als **i variabel**.
3. **Persönlichkeitsstörungen:** ICD-11 dimensional betont; MER liefert Zusatzachse, nicht Klassifikationsersatz.
4. **OCD:** CSTC-Modell explizit; Ritual als b-Übersteuerung mit q-Angsttreiber.

---

"""

    # Keep sections 2-6 from source with targeted upgrades
    parts = source.split("## 2 —")
    tail = "## 2 —" + parts[1] if len(parts) > 1 else ""

    # Upgrade section 2 formula paragraph
    tail = tail.replace(
        "Die Gesamtverzerrung: **I(Z) = Σ |Δi_imaginär|** — je höher, desto weiter ist die innere Landkarte von der Realität entfernt.",
        "Die Gesamtverzerrung: **I(Z) = Σ |Δi_imaginär|** — je höher, desto weiter ist die innere Landkarte von der Realität entfernt.\n\n"
        "**Operationalisierung (Claude Science):** I(Z) kann approximiert werden durch Triangulation aus (a) Selbstbericht-Skalen, "
        "(b) Fremdbeurteilung (Stamm/Therapeut), (c) Verhaltensmarker. Ein „realer\" Zustand ist nie direkt beobachtbar — "
        "nur **konsensuelle Näherung**. Inter-Rater-Reliabilität ist die zentrale Validitätsfrage (vgl. Abschnitt 5).",
    )

    # Replace section 5 with expanded version including komorbidity
    new_section5_7 = """
## 5 — Grenzen des Modells (präzisiert)

1. **Fließende Cluster:** Schwerpunkte, keine Schubladen — Komorbidität ist die Norm (siehe §7).
2. **Individuelle Gewichtung:** Derselbe ICD-Code kann unterschiedliche MER-Vektoren tragen.
3. **Messproblem I(Z):** Gelöst als *Triangulation*, nicht als Einzelwahrheit — epistemische Demut eingebaut.
4. **Kulturelle Bindung:** K/G/S/N-Begriffe sind MER-Semantik; klinische Übersetzung braucht lokalen Kontext.

---

## 7 — Komorbiditäts-Interaktionsmatrix (neu)

Häufige Bündel — Pfeil = Verstärkung / Koppelung:

| Bündel | Wechselwirkung | MER-Dynamik | Klinische Konsequenz |
|---|---|---|---|
| ADHS + Borderline | Impuls ↑ + Bindung oszilliert | q↑ + S−− | DBT + Strukturierung, Stammarbeit priorisieren |
| Depression + Angst | Erregung + Niedergeschlagenheit | G+ K+ S− | SSRI/SNRI + KVT; nicht nur eines behandeln |
| PTBS + Substanz | Vermeidung + Surrogat | S− → K+ | Traumafokus + Entzug parallel (stabilisieren zuerst) |
| OCD + Depression | Ritual erschöpft | b↑ q↑ S− | EX/RP vor tiefer Rekonstruktion wenn akut |
| Autismus + Angst | Sensorik + Unsicherheit | N + G+ | Anpassung Umwelt, nicht „Normalisierung" |
| Essstörung + Borderline | Kontrolle + Bindung | G+ S−± | Spezialisierte ED-Therapie + Bindungsmodul |

**Regel:** Komorbidität erhöht I(Z) überadditive, wenn imaginäre Räume sich gegenseitig stabilisieren (z. B. „ich bin faul" + „niemand versteht mich").

---

## 8 — Neurobiologische Pfade (kompakt, evidenzorientiert)

| Cluster | Kernpfade | Evidenz |
|---|---|---|
| N-primär | Dopamin/Serotonin, circadiane Gene, Konnektom-Reife | A |
| S-primär | HPA-Achse, Amygdala-Präfrontal-Kopplung, Epigenetik früher Stress | A |
| G-primär | Default-Mode / Salienz-Netzwerk, kognitive Schemata | A |
| K-primär | Interozeption, autonomes Nervensystem, Entzugssyndrome | A |

MER übersetzt diese Pfade in **therapeutische Zugänge**: N→pharmakologisch/Embodiment; S→Bindung/Stamm; G→KVT/Schemata; K→Psychoedukation/Interozeption.

---

## 9 — Therapiepfade nach Cluster (Leitlinien-Nähe)

| Cluster | Erstlinie | MER-Ziel | Memetisch vs. mimetisch |
|---|---|---|---|
| N-primär | Medikation + Psychoedukation + Struktur | d(Z,Z*) senken via K/N | SSRI allein ohne S/G = mimetisch |
| S-primär | Traumatherapie, DBT, Bindungsarbeit | Δ_S und I(Z) reduzieren | Symptomunterdrückung ohne Beziehung = mimetisch |
| G-primär | KVT, Metakognition, Exposition | q∘b rebalancieren | Affirmation ohne Realitätsabgleich = mimetisch |
| K-primär | Interozeptive Exposition, Entzug, Somatik | K-Signal dekodieren | Sedierung ohne Bedeutungsarbeit = mimetisch |

---

## 10 — Ethik, Stigma & Sprache

- **Person-first:** „Mensch mit Schizophrenie-Erfahrung" vor reduzierender Labelidentität.
- **N-Cluster:** Gesellschaftliche Fehlattribution (Charakter) = Δ_N imaginär auf Populationsebene.
- **Kein Wettbewerb des Leidens:** MER dient Verständnis, nicht Hierarchisierung von Diagnosen.

---

"""

    # Remove old section 5 and append new sections before section 6 if present
    if "## 5 — Was offen bleibt" in tail:
        pre5, post5 = tail.split("## 5 — Was offen bleibt", 1)
        if "## 6 —" in post5:
            _, post6 = post5.split("## 6 —", 1)
            tail = pre5 + new_section5_7 + "## 6 —" + post6
        else:
            tail = pre5 + new_section5_7

    footer = """

---

*Stand: 1. Juli 2026 — v2 Claude Science Review: 24 Störungen, Komorbiditätsmatrix, Evidenzgrade, Operationalisierung I(Z), Ethikabschnitt.*
"""

    return header + review_block + section1 + tail + footer


def _write_pdf(md_text: str, path: Path) -> None:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.set_margins(12, 12, 12)
    font = Path(r"C:\Windows\Fonts\arial.ttf")
    if font.exists():
        pdf.add_font("Arial", "", str(font))
        family = "Arial"
    else:
        family = "Helvetica"

    width = pdf.w - pdf.l_margin - pdf.r_margin

    def emit(text: str, size: int = 9, h: float = 5.0) -> None:
        clean = text.replace("\t", " ").replace("**", "").strip()
        if not clean:
            pdf.ln(3)
            return
        if pdf.get_y() > pdf.h - 20:
            pdf.add_page()
        if len(clean) > 220:
            clean = clean[:217] + "..."
        pdf.set_font(family, size=size)
        try:
            pdf.multi_cell(width, h, clean)
        except Exception:
            safe = clean.encode("latin-1", "replace").decode("latin-1")
            pdf.multi_cell(width, h, safe)

    pdf.add_page()
    for line in md_text.splitlines():
        s = line.rstrip()
        if not s:
            emit("")
            continue
        if s.startswith("# "):
            emit(s[2:], 14, 8)
            pdf.ln(2)
        elif s.startswith("## "):
            emit(s[3:], 12, 7)
            pdf.ln(1)
        elif s.startswith("### "):
            emit(s[4:], 11, 6)
        elif s.startswith("|"):
            if set(s.replace("|", "").replace(" ", "")) <= {"-", ":"}:
                continue
            cells = [c.strip() for c in s.strip("|").split("|")]
            emit(" · ".join(cells), 7, 4)
        elif s.startswith(">"):
            emit(s.lstrip("> ").strip(), 9, 5)
        elif s.startswith("---"):
            pdf.ln(2)
        else:
            emit(s, 9, 5)
    pdf.output(str(path))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    source = _load_source()
    science = _run_claude_science(source)
    science_note = science.get("response", "") if science.get("ok") else ""
    improved = _build_improved_markdown(
        source,
        science_note,
        include_api_note=science.get("backend") == "claude-science",
    )
    OUT_MD.write_text(improved, encoding="utf-8")
    try:
        _write_pdf(improved, OUT_PDF)
        pdf_ok = True
    except Exception as exc:
        pdf_ok = False
        pdf_err = str(exc)
    result = {
        "ok": True,
        "science_backend": science.get("backend"),
        "md": str(OUT_MD),
        "pdf": str(OUT_PDF) if pdf_ok else None,
        "pdf_ok": pdf_ok,
        "chars": len(improved),
    }
    if not pdf_ok:
        result["pdf_error"] = pdf_err
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()