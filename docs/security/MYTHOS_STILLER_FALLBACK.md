# MYTHOS — Der stille Fallback

**Domäne:** `MYTHOS` (narrativ/Geltung — `heroic_core_orchestrator.VALID_DOMAINS`)
**Anlass:** `fusion_hero_os/core/poly_mesh_cost_function.compute_burn`
**UTC:** 2026-07-27
**Geltung:** Befund = **Satz** (gemessen) · abgeleitete Regel = **Spezifikation**

## Der Befund

`compute_burn()` kapselte seine Live-Aktualisierung in

```python
try:
    ... vier Schritte: Import, Blend flagship, Blend fast, Burn-Schätzung ...
except Exception:
    ... statischer Fallback ...
```

Im ersten der vier Schritte stand ein positionaler Aufruf einer keyword-only
definierten Funktion. Der `TypeError` flog also bei **jedem einzelnen Lauf** —
und wurde jedes Mal verschluckt. Die drei folgenden Schritte liefen nie.

Gemessen bei 1M in / 300k out Tokens:

| Feld | mit stillem Fallback | nach dem Fix |
|---|---:|---:|
| `l4_llm_eur_h` | 10.4 | 6.9 |
| `l4_eur_h` | 10.4 | 6.9 |
| `llm_flagship_blend_eur_per_1m` | 8.0 | 4.37 |
| `llm_fast_blend_eur_per_1m` | 0.7 | 0.2645 |
| `llm_burn` | `{}` | volle Provider-Aufschlüsselung |

Die LLM-Kosten lagen rund **50 % zu hoch**, über unbekannte Zeit.

## Warum es niemandem auffiel

Nicht, weil niemand hinsah. Sondern weil **nichts zu sehen war**:

1. **Der Fallback lieferte plausible Zahlen.** Ein Wert von 10.4 EUR/h sieht
   nicht falsch aus. Es gab keinen Ausschlag, keine Null, keinen Absturz.
2. **Der Test prüfte die falsche Sache.** `test_llm_burn_in_compute_burn`
   verlangte `l4_llm_eur_h > 0`. Das galt im Fallback genauso. Ein grüner Test
   bestätigte einen Zweig, der nie lief.
3. **Ausgabe und Fehlerfall waren nicht unterscheidbar.** Der Rückgabewert trug
   kein Feld, das „live" von „Notbehelf" getrennt hätte.

Das ist das Muster: **breites `except` über eine mehrschrittige Operation,
plausibler Fallback, kein Marker.** Stille sieht dann aus wie Erfolg.

## Verbindung zur dritten Direktive

Ausgabe immer **Geister manifestiert** — nichts bleibt latent.

Genau das war hier verletzt, nur an anderer Stelle als im Konnektor-Automaten.
Der verschluckte `TypeError` war ein Geist im Wortsinn: wirksam, aber
unsichtbar. Er hatte Folgen (falsche Kosten), ohne je in einer Ausgabe
aufzutauchen. Ein `except Exception` ohne Marker ist eine Maschine, die Geister
erzeugt.

## Abgeleitete Regel

1. **Ein `except` fängt Umweltfehler, keine Programmierfehler.**
   `ImportError`, `LookupError`, `ValueError`, `ArithmeticError` sind Zustände
   der Welt. `TypeError`, `AttributeError`, `NameError` sind Fehler im Code und
   müssen durchschlagen.
2. **Ein Fallback muss sich zu erkennen geben.** Wer statt des Live-Werts einen
   Notbehelf liefert, schreibt das in die Ausgabe — hier
   `llm_blend_quelle: live|fallback` samt `llm_blend_fallback_grund`.
3. **Ein Test auf `> 0` ist kein Test auf den Zweig.** Prüfe, dass der Pfad
   *durchgelaufen* ist (befülltes `llm_burn`, Blend ≠ statische `RATES_EUR`),
   nicht dass die Zahl plausibel aussieht.
4. **Je breiter das `try`, desto enger das `except`.** Vier Schritte unter einem
   `except Exception` heißt: drei davon können stumm ausfallen.

## Umsetzung

- `compute_burn`: `except Exception` → `except (ImportError, LookupError,
  ValueError, ArithmeticError)`; Programmierfehler schlagen durch.
- Neue Felder `llm_blend_quelle` und `llm_blend_fallback_grund` im `detail`.
- Tests: Umweltfehler → Fallback **mit Begründung**; Programmierfehler →
  propagiert, nicht verschluckt.

## Bounds

Kein Verhalten im Erfolgsfall geändert · keine Ratenwerte angefasst ·
Fallback bleibt erhalten, wird nur sichtbar · sandbox_only

## Evidence

- `fusion_hero_os/core/poly_mesh_cost_function.py`
- `tests/test_mcp_fill_sinnkongruenz_cost.py`
- Vorgeschichte: PR #7 (keyword-only-Aufruf korrigiert)
