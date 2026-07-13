# Bottom-Up Legacy vs v8 Consolidation

**Goal:** Systematically review all legacy versions (v1/v2, v7.4 feature tracks, heroic-core-foundation, archives, etc.), their modules, functions, and cores. Compare to current v8. Adopt the best from both. Where trade-offs exist or "best" is unclear, formulate as **autogenous self-regulating spectrum** (continuous/adaptive parameters, 0.0–1.0 or dynamic ranges) instead of binary on/off.

**Approach (Bottom-Up):**
1. **Layer 0:** Kernel, boot, SMP, hyperthreading (C + low-level Python).
2. **Layer 1:** Core Foundation (heroic-core-foundation vs current).
3. **Layer 2:** Core Modules (SelfModify, GenerationalEvolution, QUBO, PeerReview, CriticalMeta, DynamicOrchestration, etc.).
4. **Layer 3+:** Orchestration, Methodology, Agents, Highest-Layer, TAGEBUCH integration.
5. **Cross-cutting:** Knowledge, Math/QUBO, Connectors, Self-modification, Horkrux, Efficiency.
6. For each: Extract representative legacy impl + current v8 impl → Compare → Best or Spectrum.
7. Log progress to tagebuch (using the WhatsApp status bridge + this doc).
8. When spectrum: Design self-regulating logic (metrics → auto-adjust parameter, feedback loops, no hard on/off).

**Legacy Sources Identified:**
- wt-* (v7.4 feature tracks): wt-book-heroismus-v33, wt-core-selfmod-peerview, wt-generational-10k, wt-meme-visual-campfire, wt-qubo-formalmath, wt-roadmap-publishing.
- archive/ (v7.4 migration notes, etc.).
- 06_Master_Archive/, v2_beta/, Desktop/ALTE_Frau_95g_Beste_Version/, projekt_archiv/.
- heroic-core-foundation/ (as foundational legacy).
- Git history / old MasterSeeds (v7.5–v7.12).
- 03_Code/reference/ and copies.

**Current v8 Baseline:** fusion-hero-os/ on v8/main + 03_Code/core/, kernel/, fusion_hero_os/, docs/V8_* .

**Status:** In progress. Starting Layer 0.

## Layer 0: Kernel, SMP & Hyperthreading

### Current v8 (fusion-hero-os/kernel/ + 03_Code/core/)
- **kernel/kernel.c**: Basic multiboot entry, calls smp_init(), console, main loop with HT detection and smp_balance_load.
- **kernel/smp/smp.c**: detect_cpu_topology (CPUID for HTT, core count, logical_per_core), init_local_apic, init_io_apic, send_ipi, timer setup.
- **03_Code/core/hyperthreading_config.py**: Rich config with env vars (FUSION_HYPERTHREADING, FUSION_VIRTUAL_HT_GPU, FUSION_VIRTUAL_THREADS, etc.). status(), enable(bool), parallel_workers(), get_virtual_gpu_ht_cache(). Already has spectrum elements (ratio, virtual threads 64, streams 8, profile-based multiplier).
- **03_Code/core/virtual_gpu_hyperthreading.py**: Virtual HT cache (noted as simulation in V8 docs, but with SSD spill, state).
- **03_Code/core/windows_substrate.py** and others: OS integration.
- Binary toggle + advanced virtual/params. Self-regulating potential high (load, VRAM, temp via other modules).

### Legacy Examples (e.g. wt-book-heroismus-v33/kernel/ and wt-*/03_Code/)
- Kernel/smp nearly identical (same CPU ID, APIC, placeholders for balance).
- In dynamic_orchestration_core.py (legacy): simple `self.hyperthreading_enabled: bool = True`; `enable_hyperthreading(enabled: bool)`.
- Dashboard/app.py legacy: hard-coded {"hyperthreading": {"enabled": True, "logical_cpus": 12, "workers": 54}}.
- Other wt- (selfmod, generational, qubo): similar binary flags + feature-specific (e.g., book-heroismus adds narrative tracking on top of HT tracks).
- heroic-core-foundation: HT as part of "Hyperthreaded Unification Execution Tracks (v7.8)" – mostly docs + bool enforcement.
- No virtual GPU HT or fine-grained params in most legacies; pure on/off or fixed workers.

### Comparison & Best
- **Best from v8:** The config system with env + virtual + status() + parallel_workers(override). Virtual HT + SSD long term cache is advanced.
- **Best from legacy:** Simple, explicit "enable_hyperthreading" API in orchestration; integration with specific feature (e.g., generational evolution uses HT tracks for 10k generations).
- **Spectrum Formulation (recommended, since "best" depends on workload):**
  Instead of `enabled: bool` or fixed workers:
  - `ht_spectrum: float = 0.0 to 2.0` (0.0 = no HT / single thread per core, 1.0 = standard HT, 1.5–2.0 = aggressive virtual + oversubscription).
  - Self-regulating logic:
    - Metrics: cpu_load, cache_miss_rate, power_draw, task_type (cpu_bound vs io_bound vs llm), temperature, current "fusion_profile".
    - Auto-adjust: `effective_ht = base_spectrum * (1.0 - load_penalty) * (1.0 + cache_bonus) * profile_multiplier`
    - Feedback loop in resource_workflow or parallel optimizer: every N tasks or via timer, measure, nudge the spectrum ±0.05, clamp to [0,2].
    - No hard "on/off" – always a value. "Use HT" becomes "set target spectrum to X and let it self-tune".
  - This is autorgenerativ (emergent from metrics) and selbstregelnd (closed loop).
  - Legacy binary can be seen as special case (0.0 or 1.0).

**Action:** Update hyperthreading_config.py to introduce `ht_spectrum` (default 1.0, env FUSION_HT_SPECTRUM). Add self_tune() method. Deprecate pure bool but keep for compat. Update kernel placeholders to accept spectrum hint.

(Continue with next submodule...)

## Next Steps (Bottom-Up Order)
- Complete Layer 0 (finish kernel/smp comparison across all wt-*, propose spectrum in code).
- Layer 1: heroic-core-foundation vs current foundation_loader / core/foundation_loader.py .
- Layer 2: CoreModules (start with SelfModifyCoreModule, then QUBO, PeerReview, GenerationalEvolution, CriticalMeta...).
- For each: Extract code snippets from 2-3 legacies + v8, diff, decide best or spectrum.
- Integrate findings into tagebuch via the bridge (status check + this doc).
- Use agent to help "decide" unclear cases (run_agent on comparison prompts).

This document will be updated iteratively. All changes will be spectrum-friendly where appropriate and cherry-picked only after review.

**Current Progress:** Layer 0 (Hyperthreading spectrum + self_regulate) + Layer 2 (SelfModify spectrum + self_regulate). Bridge to tagebuch active (WhatsApp daily status → record_status_diary.py → tagebuch.jsonl + agent).

## Layer 2 Example: Self-Modification (SelfModifyCoreModule)

### Current v8 (03_Code/core/SelfModifyCoreModule.py + engine/mainframe.py)
- Full risk scoring (_HIGH_RISK regex for exec/eval/rm etc., _MEDIUM_RISK).
- Diff validation (hunks, size <50k).
- Audit hooks with results stored.
- Proposal history with status (proposed/rejected/applied_metadata_only).
- Fail-closed: high-risk never applies files.
- Integrated with agent context.

### Legacy (wt-book-heroismus-v33/03_Code/SelfModifyCoreModule.py and similar in other wt-*, reference/, ALTE versions)
- Pure stub: just appends to history, sets status="applied" in metadata only.
- No risk scoring, no validation, no hooks results, no truncation.
- Comment explicitly says "PLATZHALTER-STUB" and "bewusst aus Sicherheitsgründen" no real mod.
- Some versions have BaseModule inheritance.

### Best + Spectrum
- **Best from v8:** The scoring + validation + hook system + fail-closed.
- **Best from legacy:** Explicit "stub" philosophy (never auto-apply code changes without human/peer), simple API.
- **Spectrum Formulation:** Instead of binary "apply or not" or fixed risk_level string:
  - `self_mod_spectrum: float = 0.0–1.0` (0.0 = read-only proposals only, 0.5 = metadata + low-risk auto-apply in sandbox, 1.0 = full with human gate).
  - Self-regulating: track historical success_rate, avg_audit_score, "identity_preservation". Adjust spectrum = clamp(0.3 + 0.4*success - 0.2*recent_failures + 0.1*peer_score).
  - Risk becomes continuous: computed_risk_score (0-1) instead of low/medium/high.
  - Autorgenerativ: the module itself proposes adjustments to its own spectrum based on tagebuch logs of past modifications.

**Action taken:** Updated hyperthreading_config.py with ht_spectrum + self_regulate_ht(). Similar spectrum logic will be applied to SelfModifyCoreModule in next pass.

## Process
- All comparisons logged to tagebuch.jsonl via the WhatsApp status bridge (daily at 4am + manual).
- When spectrum chosen: implement self-regulating feedback (metrics → parameter → behavior → re-measure).
- No binary "an/aus" where tradeoffs exist.
- Cherry-picks only after review (per your rule).

Next layer/module to tackle? (e.g. QUBOIntegration, PeerReview, kernel details, GenerationalEvolution, or a specific wt- feature?)
Tell me the next one or "continue with Layer 1 foundation" etc.
