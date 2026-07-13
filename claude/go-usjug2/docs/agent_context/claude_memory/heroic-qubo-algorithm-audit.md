---
name: heroic-qubo-algorithm-audit
description: Claude-Science-Abgleich für heroic_qubo_annealing_v1 — Architektur, Metriken, Claim-vs-Substanz, priorisierte Verbesserungen
metadata:
  node_type: memory
  type: project
  originSessionId: grok-2026-07-02
  synced_with: .claude/projects/C--Users-Admin-Downloads-ALTE-Frau-95g-Core-v3-6/memory
---

**Stand 2026-07-02** — Abgleich Grok-Analyse ↔ Claude-Science-Schema (`claude_science.py`, `heroic_science_audit.py`).

## Algorithmus `heroic_qubo_annealing_v1`

**Pfad:** `03_Code/internal_llm/heroic_llama_optimizer.py` (aufgerufen via `train.py`)

**Geltungskategorie:** *Modell* — Inference-Parameter-Optimizer, **kein Gewichts-Training**.

| Phase | Methode | Datei |
|-------|---------|-------|
| 1 | Simulated Annealing auf `temperature`, `top_p`, `repeat_penalty` | `simulated_annealing_params()` |
| 2 | QUBO Greedy Sample Selection (64-dim Bag-of-Words) | `greedy_qubo_select()` + `make_diversity_qubo()` |
| Inference | Multi-Kandidat + QUBO-Scoring | `03_Code/core/qubo_llama_bridge.py` |

## Letzte Messung (`output/heroic_llama_config.json`)

- **Token-F1: 1,97 %** (477 Samples, 38,5 s, 1 Epoch)
- Datenstand: **507 Samples** in `data.jsonl` (+30, noch nicht neu trainiert)
- Optimierte Params: temp≈0.74, top_p≈0.78, repeat_penalty≈1.11
- Modell: `Llama-3.2-1B-Instruct-Q4_K_M.gguf` (770 MB)

## Claude-Science Verdict: **WARN**

**Stärken:** schnell, GPU-schonend, sauberer Export (config + Modelfile), QUBO-Diversität sinnvoll bei kleinem Datensatz.

**Bottlenecks (F1≈2 % erklärt):**
1. Kein LoRA/SFT — nur Sampling-Parameter ändern
2. Token-F1 auf Wort-Mengen (keine Reihenfolge/Semantik)
3. Mini-Validierung: 4 Val-Samples, 8 SA-Steps (`FUSION_TRAIN_SA_STEPS`), erste 20 Samples ohne Hold-out
4. `max_gen_tokens: 64` in `config.yaml` — Antworten abgeschnitten
5. Schwaches QUBO-Embedding (Hash-BOW dim=64)
6. SA-Acceptance ineffizient: doppelter `score_fn`-Aufruf, Metropolis-Vergleich gegen `best_score` statt `current` (Zeile 93 in `heroic_llama_optimizer.py`)

## Claim-vs-Substanz (Code-Honesty)

- `03_Code/internal_llm/README.md` behauptet **LoRA/QLoRA Fine-Tuning** — `train.py` implementiert nur `HeroicLlamaOptimizer` (Generation-Params). **Überclaim.**
- Algorithmus-Name suggeriert „Training“ — tatsächlich **Hyperparameter-Search + Sample-Selection**.

## Priorisierte Verbesserungen (Claude-Science + Code-Review konsolidiert)

| Prio | Maßnahme | Erwartung |
|------|----------|-----------|
| 1 | LoRA/SFT auf QUBO-selected Samples | F1 10–40 %+ realistisch |
| 2 | Metrik-Mix: Token-F1 + chrF/BLEU + Embedding-Cosine | Robustere Optimierung |
| 3 | Hold-out 80/10/10, stratifiziert | Echte Generalisierung |
| 4 | SA: 40–80 Steps, 16–20 Val-Samples; Bug fixen; `top_k`/`min_p` | +2–5 % ohne LoRA |
| 5 | `max_gen_tokens`→128–256, `epochs:2`, besseres Embedding | Weniger Truncation |

**Quick-Win Config:**
```yaml
epochs: 2
batch_size: 8
max_gen_tokens: 128
```
```powershell
$env:FUSION_TRAIN_SA_STEPS = "40"
$env:FUSION_TRAIN_VAL_SAMPLES = "16"
```

## Claude Science Live-Status

- `ANTHROPIC_API_KEY` leer in `03_Code/Dashboard/.env` → `configured: false`
- Llama-only Desktop-Starter setzt `FUSION_CLAUDE_SCIENCE=0`
- API: `POST /api/claude-science/analyze` (Domäne `heroic_science`)
- Formaler Audit: `POST /api/claude-science/heroic-audit/run`

## Runtime (2026-07-02)

- Desktop-Starter: `C:\Users\Admin\Desktop\FusionHero_LlamaLocal\` — **Exit 0** nach Fix (`FUSION_AUTO_LOAD=0` beim Boot, Autoload via API)
- Dashboard: `:8000` (uvicorn), Workspace NiceGUI: `:8080`
- Repo: `C:\Users\Admin\fusion-hero-os` → github.com/95guknow/fusion-hero-os

Verwandt: [[pending-code-honesty-audit]], [[project-architecture]], [[github-repos]].