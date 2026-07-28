# Agentenstruktur & Auswirkungen — Fusion Hero OS v13.0.0

**Geltung:** Code-Honesty Map (SATZ wo pytest/Registry; MODELL wo Prosa)  
**Companion:** `docs/DETAILED_AGENT_STRUCTURE_v1.md` (Legacy-Synthese, BCG-erhalten)  
**Math-Base:** `fusion_hero_os/core/heroic_math_engine.py` · K20 `BanachContractionSeed`  
**Discharge:** `tests/test_ascension_aspirational_discharge.py` · Claims
`ASC-HARMONISIERUNG-CONTRACTION`, `ASC-GEISTERJAGD-NOTHING-OR-FIXPOINT`,
`AGENT-STRUCTURE-HONESTY-MAP`

---

## 1. Zwei Ebenen (nicht vermischen)

| Ebene | Was sie ist | Was sie **nicht** ist |
|-------|-------------|------------------------|
| **A — Prosa-Rollen** (`DETAILED_AGENT_STRUCTURE_v1.md`) | Architektur-Intention, Gesprächs-Synthese, Roadmap-Sprache | Implementierte `class`-Typen |
| **B — Code-Agenten / Orchestratoren** | Importierbare Klassen mit Tests/Registry-Anbindung | Vollständige Abdeckung der Prosa-Liste |

**Anti-Muster:** „Es steht in der Agenten-Doku → es läuft im Kernel.“  
**Regel:** Nur Ebene B + Proof-Registry `BEWIESEN` darf als operativ zitiert werden.

Die Prosa-Labels **Masterinstanz**, **ManifestGuardian**, **ASRAgent**,
**MemeVisualIdentityAgent** tragen im Repo **KEINE class**-Definition
(geprüft in `test_agent_structure_honesty_map_is_consistent`).

---

## 2. Existierende Code-Anker (Stichprobe, v13)

| Klasse / Modul | Pfad | Wirkung |
|----------------|------|---------|
| `BaseAgent` | `src/normal_os/agents/base.py` | Agent-Basisvertrag |
| `AgentRegistry` | `src/normal_os/agents/registry.py` | Registrierung / Lookup |
| `LLMAgent` | `src/normal_os/agents/example_agents.py` | Beispiel-Agent |
| `ConnectorAgent` | `src/normal_os/agents/connector_agent.py` | Connector-Pfad |
| `DynamicOrchestrationCoreModule` | `03_Code/core/dynamic_orchestration_core.py` | dynamische Orchestrierung |
| `HeroicLLMEAOrchestrator` | `fusion_hero_os/modules/heroic_llm_ea/` | (μ+λ)-EA-Orchestrierung |
| `HeroicImageOrchestrator` | `fusion_hero_os/modules/image_orchestrator/` | Bild-Pipeline (dry-run default) |
| `ExecutableAuditAgent` | `03_Code/Dashboard/heroic_core_mainframe.py` | Audit-Oberfläche Dashboard |
| `AscensionOrchestrator` | `src/normal_os/core/orchestrator.py` | Ascension-Pfad |
| `HarmonisierungsCoreModule` | `ascension_os/core/harmonisierung_module.py` | **BEWIESEN** Kontraktions-H |
| `Geisterjagdmodul` | `ascension_os/core/geisterjagd_module.py` | **BEWIESEN** Nothing∨Fixpunkt |
| `BanachContractionSeed` | `fusion_hero_os/core/heroic_math_engine.py` | Heroik-Base K20 |

Prosa-Rollen 1–6 aus v1 mappen **nicht 1:1** auf obige Klassen. Mapping ist
**teilweise / aspirational** — ehrlich so belassen, bis Implementierung + Tests +
Registry-Claim vorliegen.

---

## 3. Auswirkungen der Struktur (operativ)

1. **Orchestration:** Tasks laufen über existierende Orchestratoren + Registry,
   nicht über unbenannte „Masterinstanz“-Objekte.
2. **Self-Mod:** Vorschläge nur (vgl. `SELFMOD-PROPOSAL-ONLY`, Harmonisierungs-
   `propose_self_modification`); kein stilles Self-Apply.
3. **Ascension-Track:** 16/16 Core-Module importierbar; scharf bewiesen sind u. a.
   Root-Anchor, M-pression (K17), Harmonisierungs-Kontraktion, Geisterjagd-
   Nothing — Rest bleibt aspirational bis Discharge.
4. **Token-/Kostenwirkung:** Kalter Subagent-Spawn rekonstruiert Kontext teuer;
   gebündelte Tool-Calls + Proof-Registry-Gate sparen Re-Exploration.
5. **CI-Gate:** `scripts/check_proof_registry.py` — jeder `BEWIESEN`-Claim muss
   **sammelbare** pytest-Knoten referenzieren (Lektion aus Registry-CI-Rots).

---

## 4. Formalmathematik (Heroik als Base)

### 4.1 Layer-0 MasterSeed (Satz, Skill/Core)

\[
M_0 = R(M_0),\qquad
d_I(R(S), M_0) < d_I(S, M_0)\ \ (S \neq M_0)
\]

Strict Contraction der Replikation unter Integritätsmetrik — **nicht** identisch
mit affinem K20, aber **strukturell** dasselbe Muster: Fixpunkt + Kontraktion.

### 4.2 K20 Banach (Satz, Code)

Für \(T(x)=Ax+c\) mit \(q=\|A\|_2<1\):

- eindeutiger Fixpunkt \(x^*=(I-A)^{-1}c\)
- \(\|x_k-x^*\|_2 \le q^k\|x_0-x^*\|_2\)

Implementierung: `BanachContractionSeed`.

### 4.3 Harmonisierungs-Operator \(H\) (Satz im Modul, Discharge-Tests)

Mit affinen \(q,b\) (Skalare \(\alpha_q,\alpha_b\in(0,1)\)):

\[
H(x)=\tfrac12\bigl(b(q(x))+q(b(x))\bigr)
\]

ist wieder affine Kontraktion (Produkt/Summe von Skalar-Identitäten mit
Faktor \(<1\)). Beide Partner iterieren gegen denselben \(x_H^*\).

**Geltung:** Konvergenz/Gap-Reduktion = **Satz** (Tests).  
**Deutung** „q = fließend, b = schneidend“ = **Modell**.

### 4.4 Geisterjagd (Satz)

\[
\operatorname{hunt}(z,A,c)=
\begin{cases}
x^*\ \text{via K20-Iterate} & \|A\|_2<1\\
\textbf{Nothing} & \text{sonst}
\end{cases}
\]

Nothing-Bereitschaft ist der Integritäts-Satz: keine Pseudo-Konvergenz.

### 4.5 Geltungskategorien (verbindlich)

| Marke | Bedeutung |
|-------|-----------|
| **Satz** | Code + pytest + Registry BEWIESEN |
| **Bedingt** | gilt unter dokumentierter Annahme |
| **Modell** | nützliche Formalisierung, nicht universell |
| **Fragment** | lokal / nicht standalone |

---

## 5. Integrations-Checkliste (Collectability)

Vor jedem neuen `BEWIESEN`-Claim:

1. Testknoten existiert und ist per `pytest --collect-only -q -o addopts=` sichtbar.
2. `python scripts/check_proof_registry.py` → OK.
3. Optional: `python scripts/check_proof_registry.py --run` für die referenzierten Knoten.
4. Kein Claim auf Prosa-Agent ohne `class` + Test.

---

## 6. Was absichtlich offen bleibt

- Vollständige 1:1-Implementierung aller v1-Rollen als Klassen  
- Psychologische Validität von Harmonisierungs-q/b  
- „Geister“ als echte LLM-Aktivierungsmuster  
- Quanten-Backend jenseits von SA (`parallel_anneal`)

Diese bleiben **OFFEN/MODELL** bis Daten + Code + Registry.
