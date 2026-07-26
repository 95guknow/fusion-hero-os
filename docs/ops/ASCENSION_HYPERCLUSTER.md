# AscensionHypercluster — Hypercluster in allen Ascensionen

> **Stand:** v12.0.0 · 2026-07-20
> **Owner (deklariert):** Senfkorn Holding UG

## Was das ist

Der **Hyperclusterup Zitterpolymesh** (PVHT-Scheduler mit vier Lanes
CPU/MEM/GPU/QPU, `fusion_hero_os/core/zitterpolymesh.py`) als
**Ausführungsschicht des AscensionOS-Tracks**. Jede *Ascension* — eine
Kernkomponente aus `ascension_os/` — wird als Cluster-Knoten auf einer Lane
betrieben und flüssig, dependency-getrieben angefahren.

„In allen Ascensionen einrichten und operationalisieren" heißt konkret: für
jede in der Config deklarierte Ascension eine Readiness-Probe über den Cluster
fahren und den Betriebszustand **ehrlich** melden — kein Fake-Erfolg.

## Governance

| Feld | Wert |
|------|------|
| Owner | **Senfkorn Holding UG** (deklarierte Betreiber-Zuordnung, **kein** Rechts-/Registerdokument) |
| Track | `ascension` |
| Consent | Layer 0 — personenbezogene Einheiten laufen ohne aktiven Grant **fail-closed** |

## Lanes → Ascensionen

| Lane | Ascension | Modul | Consent? |
|------|-----------|-------|:---:|
| CPU | `consent-gate` | `ascension_os.consent_gate` | — |
| CPU | `ascension-core` | `ascension_os.core.ascension_core` | — |
| MEM | `persistent-sisyphos` | `ascension_os.core.persistent_sisyphos` | ✅ |
| MEM | `stage9-tracker` | `ascension_os.core.stage9_tracker` | ✅ |
| GPU | `generational-evolution` | `ascension_os.evolution.generational_engine` | — |
| QPU | `qubo-optimizer` | `ascension_os.core.qubo_ascension_optimizer` | — |

GPU-Lane ist ohne echte Hardware virtuell (CPU-Fallback), QPU-Lane immer
Simulated Annealing — das Reporting sagt das explizit (`virtual: true`).

## Consent bleibt Layer 0

Ascensionen, die personenbezogene Daten berühren (Sisyphos-Lasthistorie,
Stage-9-Tracking), sind `requires_consent: true`. Ohne aktiven Grant meldet der
Cluster sie als `blocked_consent` und weist sie **nicht** als betriebsbereit
aus — dieselbe fail-closed-Disziplin wie `ascension_os/consent_gate.py` und
`fusion_hero_os/meta/consent.py`. Ein echter Grant kommt ausschließlich aus
diesem Consent-Pfad; das `--consent-ok`-Flag spiegelt nur dessen Ergebnis.

## CLI

```bash
python -m ascension_os.hypercluster --status         # Lanes + Einheiten + Owner
python -m ascension_os.hypercluster --validate       # DAG (Zyklen/Deps) prüfen
python -m ascension_os.hypercluster --operationalize # alle Ascensionen anfahren (fail-closed)
python -m ascension_os.hypercluster --operationalize --consent-ok  # mit aktivem Grant
```

Beispiel-Lauf (Sandbox, ohne Consent-Grant):

```
ok: True | owner: Senfkorn Holding UG
summary: {operational: 4, degraded: 0, blocked_consent: 2, total: 6}
```

## Dateien

- `ascension_os/hypercluster.py` — `AscensionHypercluster`, `AscensionUnit`, CLI
- `ascension_os/config/hypercluster.yaml` — Governance + Ascension-Deklaration
- `tests/test_ascension_hypercluster.py` — 9 Tests (Lanes, DAG, Consent-Fail-Closed, Ehrlichkeit)

## Related

- Hypercluster-Kern: `zitterpolymesh.md`
- Consent-Gate: `ascension_os/consent_gate.py`
- Branch-/Merge-Governance: `docs/ops/HUMAN_CONFIRM_GATE.md`
