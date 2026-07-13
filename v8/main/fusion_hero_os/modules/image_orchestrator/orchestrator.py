"""HeroicImageOrchestrator — Visual Identity + Pipeline + Queue."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml

from fusion_hero_os.core.base_module import BaseModule, ReviewCriterion, ReviewResult
from fusion_hero_os.modules.image_orchestrator.job_queue import ImageJobQueue
from fusion_hero_os.modules.image_orchestrator.pipeline import ImagePipeline
from fusion_hero_os.modules.image_orchestrator.providers import (
    CallableImageProvider,
    DryRunImageProvider,
    ImageProvider,
)
from fusion_hero_os.modules.image_orchestrator.rate_limiter import (
    DualRateLimiter,
    RateLimitConfig,
)

_CONFIG_PATH = Path(__file__).parent / "config" / "visual_identity.yaml"


class HeroicImageOrchestrator(BaseModule):
    """
    Bild-Pipeline-Orchestrator.

    Actions: submit | status | list | configure
    """

    def __init__(self, config_path: Optional[Path] = None, provider: Optional[ImageProvider] = None) -> None:
        super().__init__()
        self.config_path = config_path or _CONFIG_PATH
        self._config = self._load_config()
        self._provider = provider or DryRunImageProvider()
        self._queue = ImageJobQueue()
        self._pipeline = self._build_pipeline()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {"identity": {}, "rate_limits": {}, "pipeline": {"mode": "dry_run"}}
        with open(self.config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _build_pipeline(self) -> ImagePipeline:
        rl = self._config.get("rate_limits", {})
        default = rl.get("default", {})
        burst = rl.get("burst", {})
        limiter = DualRateLimiter(
            RateLimitConfig(
                max_requests=int(default.get("max_requests", 10)),
                window_seconds=float(default.get("window_seconds", 60.0)),
            ),
            RateLimitConfig(
                max_requests=int(burst.get("max_requests", 3)),
                window_seconds=float(burst.get("window_seconds", 10.0)),
            ),
        )
        return ImagePipeline(self._config, limiter, self._queue, self._provider)

    def set_provider(self, provider: ImageProvider) -> None:
        self._provider = provider
        self._pipeline = self._build_pipeline()

    def process(self, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        action = payload.get("action", "submit")

        if action == "list":
            return {"action": "list", "jobs": self._queue.list_recent(int(payload.get("n", 20)))}

        if action == "status":
            job_id = str(payload.get("job_id", ""))
            job = self._queue.get(job_id)
            return {"action": "status", "job": job.to_dict() if job else None}

        if action == "configure":
            if payload.get("mode") in ("dry_run", "live"):
                self._config.setdefault("pipeline", {})["mode"] = payload["mode"]
                self._pipeline = self._build_pipeline()
            return {"action": "configure", "mode": self._config.get("pipeline", {}).get("mode")}

        prompt = str(payload.get("prompt", ""))
        result = self._pipeline.run(prompt)
        return {"action": "submit", **result}

    def peer_review(self, target: Optional[Dict[str, Any]] = None) -> ReviewResult:
        live = self._config.get("pipeline", {}).get("mode") == "live"
        has_callable = isinstance(self._provider, CallableImageProvider)
        criteria = [
            ReviewCriterion("Visual Identity YAML", self.config_path.exists()),
            ReviewCriterion("Dual Rate-Limiter", True, "default + burst"),
            ReviewCriterion("Multi-Stage Pipeline", True, "4 stages"),
            ReviewCriterion("Job-Queue", True),
            ReviewCriterion("Dry-Run default", not live),
            ReviewCriterion("Echter Bild-Provider", live and has_callable, "Opt-in + Callable"),
        ]
        return ReviewResult(module=self.name, criteria=criteria)