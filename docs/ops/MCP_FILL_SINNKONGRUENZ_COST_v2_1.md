# MCP Fill 40–70% · Sinnkongruenz-Autokompression · Provider-Realkosten → Kosten/Energie v2.1

**Stand:** 2026-07-26 · Platform **v13.0.0**  
**Cost function:** **2.1.0**  
**Geltung:** Spezifikation (Algorithmen) · Provider-Preise = **Bedingt** (public list)

## MCP Fill Band

| Parameter | Default | Env |
|-----------|---------|-----|
| Window | 128000 tokens | `FUSION_MCP_CONTEXT_WINDOW` |
| Min fill | **40%** | `FUSION_MCP_FILL_MIN` |
| Max fill | **70%** | `FUSION_MCP_FILL_MAX` |
| Target | **55%** | `FUSION_MCP_FILL_TARGET` |

**Regel:** wenn möglich `fill ∈ [0.40, 0.70]`.

- **> 70%** → Autokompression bis Target (~55%), niedrigste Sinnkongruenz zuerst  
- **< 40%** → Refill aus Archiv (höchste Kongruenz)  
- **in band** → hold  

Modul: `fusion_hero_os.core.mcp_fill_governor`

## Sinnkongruenz-Kompression **ohne Informationsverlust**

### Pipeline (streng)

1. **Lossless normalize** — Whitespace / leere Zeilen  
2. **Lossless densify** — doppelte Zeilen (order-preserving unique)  
3. **Lossless dedupe** — exakte/normalisierte Unit-Hashes  
4. **Lossless merge** — consecutive same-role → Line-Union  
5. **Reversible offload** — volle Unit nach  
   `~/.fusion-hero-os/mcp_fill/lossless_archive/<sha>.json`;  
   im Window nur Stub mit `rehydrate_from_archive(sha)`  

**Kein permanenter Drop.** `dropped` ist immer 0; `information_loss=false`.

### Score (nur Reihenfolge des Offloads)

\[
s = 0.28\,w_{\mathrm{role}} + 0.18\,r_{\mathrm{recency}} + 0.42\,J_{\mathrm{intent}} + 0.12\,a_{\mathrm{anchors}} - L_{\mathrm{verbose}}
\]

- \(J\) = Jaccard Intent↔Content (dominant)  
- Niedrige \(s\) → zuerst **offload** (nicht löschen)  
- `pin` / MasterSeed → nie offload  

Modul: `fusion_hero_os.core.sinnkongruenz_compressor`  
Rehydrate: `rehydrate_from_archive(hash_id)`

## Provider-Realkosten (Top)

Public list prices (USD/1M → EUR via `FUSION_USD_EUR=0.92`), blend 70% in / 30% out.

| Tier | Beispiele | Nutzung intern |
|------|-----------|----------------|
| fast | Gemini Flash, GPT-4o mini, Grok Fast | mesh_ops ceilings |
| flagship | Sonnet, GPT-4o/4.1, Gemini Pro, Grok 4 | inference_standard ceilings |
| frontier | Opus | qubo_enterprise upper |

Modul: `fusion_hero_os.core.provider_token_costs`

## Kosten-/Energiefunktion v2.1

\[
C_h = C_{L1}+C_{L2}+C_{L3}+C_{L4},\quad
C_{L4}=\mathrm{saas}+\mathrm{LLM}(\mathrm{tokens},\,\mathrm{provider\_rates})
\]

Market ceilings für Subunternehmer-Preise werden aus Provider-Output-Medians **überlagert** (wenn nicht explizit im Businessplan gesetzt).

## MCP Tools

| Tool | Zweck |
|------|--------|
| `fhero_mcp_fill_govern` | Fill-Band + Kompression |
| `fhero_provider_costs` | Realkosten-Analyse + optional cost_function_status |

## API / CLI

```powershell
python -c "from fusion_hero_os.core.provider_token_costs import analyse_providers; import json; print(json.dumps(analyse_providers(), indent=2)[:2000])"
python -c "from fusion_hero_os.core.poly_mesh_cost_function import cost_function_status; print(cost_function_status()['cost_function_version'])"
python -c "from fusion_hero_os.core.mcp_fill_governor import govern_messages; print(govern_messages([{'role':'user','content':'x'*50000},{'role':'assistant','content':'y'*50000}], intent='QUBO mesh')['fill'])"
```
