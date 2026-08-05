# Kostenfunktion v2.1 — Poly-Mesh L0–L4 + Provider-Token-Ceilings

**Stand:** 2026-07-26 · Fusion Hero OS **v13.0.0**  
**Businessplan:** `docs/business/senfkorn_businessplan.yaml` (v1.3)  
**Modul:** `fusion_hero_os.core.poly_mesh_cost_function` (**2.1.0**)  
**Provider-Raten:** `fusion_hero_os.core.provider_token_costs` (Bedingt)  
**MCP Fill:** `fusion_hero_os.core.mcp_fill_governor` · Sinnkongruenz-Kompressor  
**Daemons:** `mainframe_cost_analysis_daemon` · `mainframe_energy_pricing_daemon`  
**Ops-Doc:** `docs/ops/MCP_FILL_SINNKONGRUENZ_COST_v2_1.md`

## Formale Definition

\[
\begin{aligned}
C_h &= C_{L1} + C_{L2} + C_{L3} + C_{L4} && \text{[EUR/h]} \\
E_h &= \frac{C_h}{p_{\mathrm{grid}}}\cdot \mathrm{PUE} && \text{[kWh-Äq/h]} \\
\mathrm{FEU}_h &= C_h \cdot \lambda_{\mathrm{FEU}} && \text{[FEU/h]} \\
c_{1k}(t) &= \frac{C_h}{\kappa(t)}\cdot 1000 \\
P_{1k}(t) &= \max\bigl(P_{\min},\; \min\bigl(c_{1k}(t)\,(1+m^\*(t)),\; \mathrm{ceiling}_{1k}(t)\bigr)\bigr) \\
\Pi(\mathrm{tier}) &= \pi_{\mathrm{base}}[\mathrm{tier}]\cdot(1+\mathrm{load}) && \text{soft only}
\end{aligned}
\]

Hard constraints (unverändert): `force_cluster` → L3 · Control Plane → L1 · Audio mesh-only 100.x.

## Layer-Burn

| Layer | Modell |
|-------|--------|
| L0 | Endgerät — nicht als Infra-Burn |
| L1 | `l1_desk_power_hour` (0.08 EUR/h) |
| L2 | `n_exit · e2_micro_hour` |
| L3 | Training-Pods + Coordination-Jobs + GPU |
| L4 | Soft SaaS-Estimate wenn aktiv |

## Subunternehmer-Tiers (v1.2)

| Tier | Use-case |
|------|----------|
| inference_standard | Chat / light |
| inference_gpu | GPU |
| qubo_enterprise | A100 / heavy |
| mesh_ops | Fractal / exit |
| **poly_mesh_orchestration** | L3 light task (CPU) |

Default-Marge **150 %** kompetitiv, Floor **35 %**, Marktdecken pro Tier.

## CLI / API

```powershell
python -m fusion_hero_os.core.poly_mesh_cost_function --status
# Dashboard up:
curl http://127.0.0.1:8000/api/v1/business/cost-function
```

## Live-Beispiel (Idle, 2026-07-16)

- \(C_h \approx 0.09\text{–}0.10\) EUR/h (L1 desk + L2 exit)
- \(\mathrm{FEU}_h \approx 9\text{–}10\)
- Headline floor price often hits \(P_{\min}=0.002\) EUR/1k when idle capacity high

## GCP Billing (kanonisch)

| Feld | Wert |
|------|------|
| Account | `YOUR_GCP_BILLING_ACCOUNT_ID` (operator-lokal, siehe .env) |
| Project | `YOUR_GCP_PROJECT` |
| **Budget** | **Senfkorn Ops 200 EUR/Monat** |
| Betrag | **200 EUR** · calendar **month** |
| Schwellen | 50 % / 90 % / 100 % CURRENT · 90 % FORECASTED |
| Aligns | `financial_targets.monthly_infra_ceiling_eur: 200` |
| Console | https://console.cloud.google.com/billing/YOUR_GCP_BILLING_ACCOUNT_ID/budgets |

Modell-Idle ~74 €/Monat liegt **unter** dem 200-€-Budget.
