"""Tests für vertiefte GROK_EXPORT-Module."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CODE = ROOT / "03_Code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from TokenManagementSystem import ResourceState, TransformationType  # noqa: E402

from fusion_hero_os.modules.timespace_token import (
    Timescale,
    TimespaceCoordinate,
    TimespaceTokenCoreModule,
    TimespaceTokenManager,
    TimespaceTrack,
)
from fusion_hero_os.modules.timespace_token.bottleneck import qubo_energy, build_competition_qubo
from fusion_hero_os.modules.heroic_llm_ea import HeroicLLMEAOrchestrator
from fusion_hero_os.modules.heroic_llm_ea.providers import CampfireTemplateProvider
from fusion_hero_os.modules.image_orchestrator import HeroicImageOrchestrator
from fusion_hero_os.modules.image_orchestrator.rate_limiter import DualRateLimiter, RateLimitConfig
from fusion_hero_os.modules.image_orchestrator.prompt_builder import build_prompt, validate_identity
from fusion_hero_os.core.dispatcher import build_default_dispatcher


# --- Timespace ---

def test_timespace_near_beats_far():
    manager = TimespaceTokenManager(base_tokens=1000)
    tracks = [
        TimespaceTrack("near", TimespaceCoordinate(0.0, 0.0), ResourceState(0.9, 0.1, 1, 0.1, 0.1)),
        TimespaceTrack("far", TimespaceCoordinate(6.0, 4.0), ResourceState(0.7, 0.3, 2, 0.2, 0.2)),
    ]
    alloc = manager.allocate(tracks)
    assert alloc["near"] >= alloc["far"]


def test_timespace_fidelity_for_meme_near_origin():
    manager = TimespaceTokenManager(base_tokens=2000)
    meme = TimespaceTrack(
        "meme",
        TimespaceCoordinate(0.1, 0.0, Timescale.MACRO),
        ResourceState(0.9, 0.1, 4, 0.05, 0.05),
        TransformationType.MEME_SYNTHESIS,
    )
    report = manager.allocate_with_report([meme])
    assert report.fidelity_applied.get("meme") is True


def test_timespace_qubo_energy_computed():
    q = build_competition_qubo(["a", "b"], {"a": 0.2, "b": 0.8})
    e = qubo_energy(q, [1, 0])
    assert e >= 0


def test_timespace_base_module_allocate():
    mod = TimespaceTokenCoreModule()
    out = mod.process({
        "tracks": [{
            "name": "t1",
            "coordinate": {"time_index": 0, "space_depth": 0, "timescale": "meso"},
            "state": {"stability": 0.8, "latent_tension": 0.2, "depth": 1,
                      "fluctuation_severity": 0.1, "bottleneck_risk": 0.1},
        }],
    })
    assert "allocations" in out
    assert out["allocations"]["t1"] >= 10


# --- HeroicLLM-EA ---

def test_llm_ea_stub_propose():
    orch = HeroicLLMEAOrchestrator()
    result = orch.process({"prompt": "campfire", "n_proposals": 2})
    assert result["best"]["fitness"] > 0
    assert result["status"] == "stub_llm"


def test_llm_ea_campfire_templates_peer_review():
    orch = HeroicLLMEAOrchestrator.with_campfire_templates()
    result = orch.process({
        "prompt": "sisyphos cycle",
        "n_proposals": 3,
        "theme": "campfire",
    })
    assert result["status"] == "campfire_templates"
    assert "peer_review_score" in result["best"] or result["best"]["fitness"] > 0


def test_llm_ea_multi_generation_evolve():
    orch = HeroicLLMEAOrchestrator.with_campfire_templates()
    out = orch.process({"action": "evolve", "n_generations": 2, "prompt": "heroic core"})
    assert out["generations_run"] == 2
    assert out["final_best"] is not None


def test_llm_ea_memory_lineage():
    orch = HeroicLLMEAOrchestrator()
    orch.process({"action": "evolve", "n_generations": 1, "prompt": "x", "n_proposals": 2})
    status = orch.process({"action": "status"})
    assert status["memory"]["total"] >= 1


# --- Image Orchestrator ---

def test_image_pipeline_submit():
    orch = HeroicImageOrchestrator()
    result = orch.process({"prompt": "cyberpunk campfire"})
    assert result["ok"] is True
    assert result["render"]["would_execute"] is False
    assert "validate_identity" in result["stages_completed"]


def test_image_job_status_and_list():
    orch = HeroicImageOrchestrator()
    sub = orch.process({"prompt": "test"})
    job_id = sub["job"]["job_id"]
    st = orch.process({"action": "status", "job_id": job_id})
    assert st["job"]["job_id"] == job_id
    lst = orch.process({"action": "list", "n": 5})
    assert len(lst["jobs"]) >= 1


def test_prompt_builder_and_validation():
    identity = {"name": "ALTE_Frau_95g", "style_tags": ["cyberpunk"], "primary_seed": "seed1"}
    built = build_prompt("campfire", identity)
    assert "cyberpunk" in built
    assert validate_identity(identity)["valid"] is True


def test_dual_rate_limiter_burst():
    limiter = DualRateLimiter(
        RateLimitConfig(max_requests=10, window_seconds=60),
        RateLimitConfig(max_requests=1, window_seconds=10),
    )
    assert limiter.allow()[0] is True
    assert limiter.allow()[0] is False


def test_dispatcher_registers_deepened_modules():
    d = build_default_dispatcher()
    names = d.list_modules()
    assert "HeroicLLMEAOrchestrator" in names
    assert "HeroicImageOrchestrator" in names
    assert "TimespaceTokenCoreModule" in names