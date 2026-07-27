# Sprachbindung — Ist gegen Soll

Platform 13.0.0 · `python -m fusion_hero_os.core.translate_controller`

**UTC:** 2026-07-27T14:14:57.028592+00:00  
**Module:** 1078 · **Abweichungen:** 11 — davon **3 durch Bindung geschlossen**, **8 offen**

Der Controller übersetzt nichts. Er ordnet zu und weist die Lücke aus.

Eine Abweichung ist nur dann Arbeit, wenn das Modul die Zielsprache nicht bereits über die vorgesehene Bindung aufruft.

## Verteilung

| Sprache | ist | soll |
|---|---:|---:|
| asm | 5 | 5 |
| c | 49 | 49 |
| js | 1 | 1 |
| python | 1021 | 1010 |
| rust | 2 | 13 |

## Lücken

| Modul | ist | soll | Regel | Bindung |
|---|---|---|---|---|
| `src/normal_os/ascension/reference/heroic_core_mainframe.py` | python | rust | heisser_pfad | pyo3_cdylib |
| `src/normal_os/ascension/tools/qb_qubo.py` | python | rust | heisser_pfad | pyo3_cdylib |
| `src/normal_os/integration/qb_qubo.py` | python | rust | heisser_pfad | pyo3_cdylib |
| `src/normal_os/math/qb_qubo.py` | python | rust | heisser_pfad | pyo3_cdylib |
| `src/normal_os/tools/qb_qubo.py` | python | rust | heisser_pfad | pyo3_cdylib |
| `03_Code/StarrLernenderAntiLoopGuardCoreModule_v1.py` | python | rust | heisser_pfad | pyo3_cdylib |
| `03_Code/reference/heroic_core_mainframe.py` | python | rust | heisser_pfad | pyo3_cdylib |
| `03_Code/tools/qb_qubo.py` | python | rust | heisser_pfad | pyo3_cdylib |

### Signale

- **heisser_pfad** — Python-Modul nutzt numba/@jit — der Code sagt selbst, dass er einen Compiler braucht. Das ist der belegte Rust-Kandidat.

## Durch Bindung geschlossen

Diese Module weichen ab, rufen die Zielsprache aber bereits auf:

| Modul | ist | soll | Bindung |
|---|---|---|---|
| `fusion_hero_os/engine/mainframe.py` | python | rust | pyo3_cdylib |
| `src/normal_os/ascension/reference/mainframe.py` | python | rust | pyo3_cdylib |
| `03_Code/reference/mainframe.py` | python | rust | pyo3_cdylib |

**Geltung:** Ist-Sprache = Satz (aus dem Dependency-Atlas bzw. der Dateiendung abgelesen) · Soll-Sprache = Spezifikation (Regel, nicht Messung) · Luecke = Bedingt, solange die Zielsprache nicht gebaut und gebunden ist
