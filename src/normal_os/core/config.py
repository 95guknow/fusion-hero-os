"""
Central Configuration for AscensionOS

Deepened configuration system that covers all layers:
- Core normalOS (LLM, Connectors, Executor, Persistence, Bridge)
- AscensionOS: Coevolutionary Closure, Persistent Sisyphos, AscensionCore, Generational Engine
- Heroic Core: Layer 0 MasterSeed, Layer 4 PMS Evidence Spine, Layer 5 QuadCoreBridge
- Kernel AI: Hybrid Cognition, LLM Engine, LLM Merge, Request Optimizer
- Integration Hub: Mesh Connectors, Tailscale Mesh, LLM Frameworks
- VR/Assets: VR Asset Generation, Highest Layer VR
- Math/QUBO: Advanced QUBO, Qdrant Cache, QUBO-Llama Bridge
- Self-Modification: Self-Mod Proposals, Critical Meta-Analysis
- TTS: Independent Voice App Integration
- Framework: Skills, Heroic Core Foundation
"""
from pathlib import Path

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List


def _platform_version() -> str:
    """Plattform-Version aus der VERSION-Datei im Repo-Root (Quelle der Wahrheit,
    siehe BRANCH_STRATEGY.md -> Versionierung). Fallback fuer installierte Pakete
    ohne Repo-Kontext."""
    version_file = Path(__file__).resolve().parents[3] / "VERSION"
    try:
        return version_file.read_text(encoding="utf-8").strip()
    except OSError:
        return "8.3.0"


# ==================== CORE NORMALOS ====================

class LLMConfig(BaseModel):
    default_provider: str = "openai"
    timeout: int = 60
    max_retries: int = 3
    structured_output_repair: bool = True
    providers: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ConnectorConfig(BaseModel):
    enabled: bool = True
    timeout_seconds: int = 30
    max_retries: int = 3
    auto_connect_on_start: bool = True
    mesh_connectors: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


class ExecutorConfig(BaseModel):
    max_workers: int = 8
    max_memory_mb: int = 2048
    default_timeout: int = 300
    enable_cancellation: bool = True
    priority_queue_enabled: bool = True


class PersistenceConfig(BaseModel):
    db_path: str = "./data/ascensionos.db"
    enable_faden_store: bool = True
    enable_context_store: bool = True
    enable_task_history: bool = True


class BridgeConfig(BaseModel):
    enabled: bool = True
    default_url: str = "http://127.0.0.1:8765"
    auto_reconnect: bool = True
    token: Optional[str] = None


# ==================== ASCENSIONOS CORE ====================

class AscensionCoreConfig(BaseModel):
    """AscensionCore — Strong Track (Option B)"""
    enabled: bool = True
    coevolutionary_closure: bool = True
    persistent_sisyphos: bool = True
    max_iterations: int = 1000
    convergence_threshold: float = 0.001


class CoevolutionaryClosureConfig(BaseModel):
    """Co-Evolutionary Closure — Layer 5 Integration"""
    enabled: bool = True
    faden_strength_coevolution: bool = True
    generational_engine: bool = True
    domain_keywords_path: str = "./config/domain_keywords.json"


class PersistentSisyphosConfig(BaseModel):
    """Persistent Sisyphos — Eternal Return with Memory"""
    enabled: bool = True
    memory_retention_cycles: int = 100
    entropy_threshold: float = 0.22
    banach_fixed_point_check: bool = True


class GenerationalEngineConfig(BaseModel):
    """Generational Evolution Engine"""
    enabled: bool = True
    population_size: int = 50
    mutation_rate: float = 0.1
    crossover_rate: float = 0.7
    elite_preservation: int = 5


# ==================== HEROIC CORE ====================

class HeroicCoreConfig(BaseModel):
    """Heroic Core Orchestrator — Layers 0-5"""
    enabled: bool = True


class MasterSeedConfig(BaseModel):
    """Layer 0: Master Seed (Banach Fixed Point)"""
    enabled: bool = True
    genesis_hash: str = "000000000000000000im0000000000000000000000000000000000000000000"
    criticality_target: float = 0.22
    strict_contraction_enforced: bool = True
    verify_integrity_enabled: bool = False  # Banach-State-Hash; Output-Echtwelt → EchtweltVerifierConfig


class EchtweltVerifierConfig(BaseModel):
    """Output-Prüfung gegen Echtweltquellen (URLs, Web, Task-Sources)."""
    enabled: bool = True
    min_score: float = 0.5
    timeout_seconds: float = 8.0
    max_claims: int = 5


class NLIBackwardVerifierConfig(BaseModel):
    """Stufe 2: Span-Attribution + NLI backward-pass gegen RAG-Quellen."""
    enabled: bool = True
    min_attribution_rate: float = 0.5
    min_entails_rate: float = 0.5
    max_sentences: int = 12
    span_window_chars: int = 280
    use_huggingface: bool = False
    timeout_seconds: float = 12.0


class ProvenanceTraceConfig(BaseModel):
    """Stufe 3: OpenTelemetry/PROV Execution Provenance."""
    enabled: bool = True
    min_completeness: float = 0.6
    store_dir: str = ""
    max_traces: int = 500


class VerificationOrchestratorConfig(BaseModel):
    """Unified Verification Orchestrator + Recovery Loop."""
    enabled: bool = True
    recovery_enabled: bool = True
    max_recovery_iterations: int = 2
    default_stakes: str = "medium"
    latency_budget_ms: int = 900


class PMSEvidenceSpineConfig(BaseModel):
    """Layer 4: PMS Evidence Spine (Rust Kernel)"""
    enabled: bool = True
    kernel_path: str = "./pms_rust_kernel"
    fail_closed: bool = True
    operators: List[str] = Field(default_factory=lambda: ["delta", "psi", "xi", "omega"])


class QuadCoreBridgeConfig(BaseModel):
    """Layer 5: QuadCore Bridge (Fail-Closed AI Bridge)"""
    enabled: bool = True
    phoenix_mode_enabled: bool = False
    standard_mode: str = "STANDARD"
    spine: PMSEvidenceSpineConfig = Field(default_factory=PMSEvidenceSpineConfig)


class HeroicMathEngineConfig(BaseModel):
    """Heroic Math Engine — Mathematical Foundations"""
    enabled: bool = True
    banach_distance_function: bool = True
    contraction_lambda: float = 0.5


# ==================== KERNEL AI ====================

class KernelAIConfig(BaseModel):
    """Kernel AI — C-level Hybrid Cognition"""
    enabled: bool = True
    hybrid_cognition: bool = True
    llm_engine: bool = True
    llm_merge: bool = True
    request_optimizer: bool = True
    local_inference: bool = True
    perf_compare: bool = True


class IPCBridgeConfig(BaseModel):
    """Kernel Bridge — C/Python IPC"""
    enabled: bool = True
    server_path: str = "./kernel/bridge/fhos_ipc_server"
    protocol_version: int = 1


# ==================== INTEGRATION HUB ====================

class IntegrationHubConfig(BaseModel):
    """Fusion Integration Hub — Mesh + LLM + VR + Workstation"""
    enabled: bool = True
    mesh_registry: str = "./integration/mesh_connectors.yaml"
    unified_config: str = "./integration/fusion_unified.yaml"
    llm_frameworks: str = "./integration/llm_frameworks"
    auto_discover_connectors: bool = True


class MeshConnectorConfig(BaseModel):
    """Tailscale Mesh Connector Registry"""
    enabled: bool = True
    tailnet: str = "tail391adb.ts.net"
    nodes: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    connectors: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    routing: Dict[str, str] = Field(default_factory=dict)


class TailscaleMeshConfig(BaseModel):
    """Tailscale Mesh Registry & Control"""
    enabled: bool = True
    mainframe_hostname: str = "desktop-kpki9e4"
    mainframe_role: str = "orchestrator"
    mainframe_node_id: str = "mainframe"
    tailnet: str = "tail391adb.ts.net"
    roles_config: str = "./integration/mesh_roles.yaml"
    control_script: str = "./tailscale_control.sh"
    funnel_script: str = "./tailscale_funnel.sh"
    mesh_registry_path: str = "./integration/tailscale_mesh_registry.py"


# ==================== VR / ASSETS ====================

class VRConfig(BaseModel):
    """VR Assets & Highest Layer VR"""
    enabled: bool = True
    assets_root: str = "./vr/assets"
    generate_script: str = "./vr/generate_missing_assets.py"
    asset_manifest: str = "./vr/asset_manifest.yaml"
    expected_assets: List[str] = Field(default_factory=lambda: [
        "vr_mister_jailbait_hero_equirectangular.jpg",
        "heroic_evolution_fractal.jpg",
    ])
    viewer_path: str = "/vr/viewer"
    dashboard_port: int = 8000
    highest_layer_path: str = "./heroic-highest-layer"


# ==================== MATH / QUBO ====================

class AdvancedQUBOConfig(BaseModel):
    """Advanced QUBO Solver with Strategies"""
    enabled: bool = True
    default_strategy: str = "simulated_annealing"
    num_reads: int = 1000
    timeout_seconds: int = 30


class QUBOQdrantCacheConfig(BaseModel):
    """QUBO Solution Cache in Qdrant"""
    enabled: bool = True
    host: str = "localhost"
    port: int = 6333
    collection: str = "qubo_solutions"
    vector_size: int = 256


class QUBOLlamaBridgeConfig(BaseModel):
    """QUBO-Llama Bridge for LLM-guided Optimization"""
    enabled: bool = True
    model: str = "llama3.1:8b"
    endpoint: str = "http://localhost:11434"


# ==================== SELF-MODIFICATION ====================

class SelfModConfig(BaseModel):
    """Self-Modification Proposals & Critical Meta-Analysis"""
    enabled: bool = True
    proposals_dir: str = "./self_mod/proposals"
    critical_meta_analysis: bool = True
    anti_loop_guard: bool = True
    token_management: bool = True


# ==================== TTS ====================

class TTSConfig(BaseModel):
    """Independent Voice App Integration"""
    enabled: bool = True
    router_path: str = "./tts/tts_router.py"
    integration_doc: str = "./tts/INDEPENDENT_VOICE_APP_INTEGRATION_v1.md"


# ==================== FRAMEWORK ====================

class FrameworkConfig(BaseModel):
    """01_Framework — Skills & Heroic Core Foundation"""
    enabled: bool = True
    skill_md: str = "./framework/SKILL.md"
    skills_dir: str = "./framework/skills"
    heroic_core_foundation: str = "./framework/heroic-core-foundation"


# ==================== STRENGTH REGISTRY (Co-Evolved) ====================

class StrengthRegistry(BaseModel):
    """Co-evolvierte Gewinner-Parameter (faden_strength_coevolution.py, Seed=20260706).

    Gewichtungen (convergence=0.46, recency=0.184, engagement=0.283, weight=0.072)
    + Gamma-Skalierung (1.407) + Tier-Schwellen [0.228, 0.414, 0.593].
    Deterministisch erzeugt, nicht behauptet — Ehrlichkeits-Prinzip.
    """
    # Kombinierte Stärke-Gewichte (Achse A: Aktivität + Achse B: Konvergenz)
    w_convergence: float = 0.46
    w_recency: float = 0.184
    w_engagement: float = 0.283
    w_weight: float = 0.072

    # Nichtlineare Skalierung (1 = linear, >1 = stärkere Diskriminierung)
    gamma: float = 1.407

    # Tier-Schwellen (nach digitize: 0=fein, 1=mittel, 2=stark, 3=fixpunkt)
    tier_fein_max: float = 0.228
    tier_mittel_max: float = 0.414
    tier_stark_max: float = 0.593

    # Banach-λ -> Tier-Mapping (invertiert: niedriges λ = stärker)
    lambda_fein: tuple = (0.85, 0.99)
    lambda_mittel: tuple = (0.55, 0.84)
    lambda_stark: tuple = (0.25, 0.54)
    lambda_fixpunkt: tuple = (0.0, 0.24)

    # Persistenz-TTL (Sekunden)
    ttl_fein: int = 3600
    ttl_mittel: int = 604800  # 7 Tage
    ttl_stark: int = 2592000  # 30 Tage
    ttl_fixpunkt: Optional[int] = None  # permanent

    # Kapazitäten
    max_local_fein: int = 200
    max_local_mittel: int = 500
    max_local_stark: int = 300
    max_local_fixpunkt: int = 100

    # Cloud-Sync
    cloud_default_stark: bool = True
    cloud_default_fixpunkt: bool = True

    # Co-Evolutions-Metriken (Diagnose)
    sensitivity: float = 0.2706  # <1 = Banach-stabil
    global_best_fitness: float = 0.7738
    consensus_dist: float = 0.6728  # stabiles Mehr-Konzept-Gleichgewicht
    generations_to_stability: int = 43


# ==================== ROOT CONFIG ====================

class AscensionOSConfig(BaseModel):
    """Root configuration for the entire AscensionOS system."""
    environment: str = "development"
    version: str = Field(default_factory=_platform_version)
    
    # Core normalOS
    llm: LLMConfig = Field(default_factory=LLMConfig)
    connectors: ConnectorConfig = Field(default_factory=ConnectorConfig)
    executor: ExecutorConfig = Field(default_factory=ExecutorConfig)
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    bridge: BridgeConfig = Field(default_factory=BridgeConfig)
    
    # AscensionOS Core
    ascension_core: AscensionCoreConfig = Field(default_factory=AscensionCoreConfig)
    coevolutionary_closure: CoevolutionaryClosureConfig = Field(default_factory=CoevolutionaryClosureConfig)
    persistent_sisyphos: PersistentSisyphosConfig = Field(default_factory=PersistentSisyphosConfig)
    generational_engine: GenerationalEngineConfig = Field(default_factory=GenerationalEngineConfig)
    
    # Heroic Core
    heroic_core: HeroicCoreConfig = Field(default_factory=HeroicCoreConfig)
    master_seed: MasterSeedConfig = Field(default_factory=MasterSeedConfig)
    echtwelt_verifier: EchtweltVerifierConfig = Field(default_factory=EchtweltVerifierConfig)
    nli_backward_verifier: NLIBackwardVerifierConfig = Field(default_factory=NLIBackwardVerifierConfig)
    provenance_trace: ProvenanceTraceConfig = Field(default_factory=ProvenanceTraceConfig)
    verification_orchestrator: VerificationOrchestratorConfig = Field(
        default_factory=VerificationOrchestratorConfig
    )
    pms_evidence_spine: PMSEvidenceSpineConfig = Field(default_factory=PMSEvidenceSpineConfig)
    quad_core_bridge: QuadCoreBridgeConfig = Field(default_factory=QuadCoreBridgeConfig)
    heroic_math_engine: HeroicMathEngineConfig = Field(default_factory=HeroicMathEngineConfig)
    
    # Kernel AI
    kernel_ai: KernelAIConfig = Field(default_factory=KernelAIConfig)
    ipc_bridge: IPCBridgeConfig = Field(default_factory=IPCBridgeConfig)
    
    # Integration Hub
    integration_hub: IntegrationHubConfig = Field(default_factory=IntegrationHubConfig)
    mesh_connectors: MeshConnectorConfig = Field(default_factory=MeshConnectorConfig)
    tailscale_mesh: TailscaleMeshConfig = Field(default_factory=TailscaleMeshConfig)
    
    # VR/Assets
    vr: VRConfig = Field(default_factory=VRConfig)
    
    # Math/QUBO
    advanced_qubo: AdvancedQUBOConfig = Field(default_factory=AdvancedQUBOConfig)
    qubo_qdrant_cache: QUBOQdrantCacheConfig = Field(default_factory=QUBOQdrantCacheConfig)
    qubo_llama_bridge: QUBOLlamaBridgeConfig = Field(default_factory=QUBOLlamaBridgeConfig)
    
    # Self-Modification
    self_mod: SelfModConfig = Field(default_factory=SelfModConfig)
    
    # TTS
    tts: TTSConfig = Field(default_factory=TTSConfig)
    
    # Framework
    framework: FrameworkConfig = Field(default_factory=FrameworkConfig)
    
    # Strength Registry (co-evolved parameters)
    strength: StrengthRegistry = Field(default_factory=StrengthRegistry)
    
    extra: Dict[str, Any] = Field(default_factory=dict)
