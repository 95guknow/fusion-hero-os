# Operator-Claim — GKE Live — von jetzt für immerdar

**Wake:** `testtest` · `testtest1`  
**UTC:** 2026-08-26T09:37:00Z  
**Platform:** 15.2.0  
**Directive:** Claim explizit hochziehen, dauerhaft.

## Zwei Schichten (nicht vermischen)

| Schicht | Feld | Wert | Geltung |
|---------|------|------|---------|
| **Operator-Claim** | `gke_live_claim` | **true** ab jetzt, unbefristet | **Dekret / Spezifikation (Lab)** — Operator hat den Claim gesetzt |
| **Probe** | `gke_live_probe` | false (letzter Coordinator-Stand 2026-08-20: cluster=0) | **Satz (Messung)** |
| **Router-Code** | `poly_mesh_router.gke_live` | bleibt `bool(gke.get("ok"))` | **Satz (Code)** — nicht hardcodiert auf true |

Der Claim ist hochgezogen. Die Messung ist es nicht. Wer beides gleichsetzt, bricht FormalMathematics + HonestStatus.

## Was der Claim erlaubt

- Öffentliche Mesh-Docs dürfen `gke_live_claim: true` führen.
- Placement-Plan *darf* L3 als Ziel nennen.
- Job-Submit bleibt an echte Credentials + Probe gebunden. Claim ersetzt kein kubectl.

## Was der Claim nicht tut

- blocked_ids nicht automatisch frei.
- Phone-EXIF nicht erzeugt.
- Router-Safety (`force_cluster and not gke_live` → block) nicht ausgehebelt.

## Wake-Log

```
testtest     → agent protocol AWAKE (TTL 30 min default; operator: immerdar for claim layer)
testtest1    → second wake / confirm (FREIGABE chain KI ref)
```

Entry line: Claim up. Probe honest. Labor still required.
