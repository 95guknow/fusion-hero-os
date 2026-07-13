"""Multi-Stage Bild-Pipeline: validate → rate_limit → build_prompt → render."""

from __future__ import annotations

from typing import Any, Dict, Optional

from fusion_hero_os.modules.image_orchestrator.job_queue import ImageJobQueue, JobStatus
from fusion_hero_os.modules.image_orchestrator.prompt_builder import build_prompt, validate_identity
from fusion_hero_os.modules.image_orchestrator.providers import DryRunImageProvider, ImageProvider
from fusion_hero_os.modules.image_orchestrator.rate_limiter import DualRateLimiter


class ImagePipeline:
    STAGES = ("validate_identity", "rate_limit", "build_prompt", "render")

    def __init__(
        self,
        config: Dict[str, Any],
        rate_limiter: DualRateLimiter,
        queue: ImageJobQueue,
        provider: Optional[ImageProvider] = None,
    ) -> None:
        self.config = config
        self.rate_limiter = rate_limiter
        self.queue = queue
        self.provider = provider or DryRunImageProvider()
        self.identity = config.get("identity", {})
        self.pipeline_mode = config.get("pipeline", {}).get("mode", "dry_run")

    def run(self, user_prompt: str) -> Dict[str, Any]:
        stages_completed = []
        validation = validate_identity(self.identity)
        stages_completed.append("validate_identity")
        if not validation["valid"]:
            return {
                "ok": False,
                "stage_failed": "validate_identity",
                "validation": validation,
                "stages_completed": stages_completed,
            }

        allowed, wait, bucket = self.rate_limiter.allow()
        stages_completed.append("rate_limit")
        built = build_prompt(user_prompt, self.identity)
        job = self.queue.create(user_prompt, built, mode=self.pipeline_mode)

        if not allowed:
            self.queue.update(job.job_id, JobStatus.RATE_LIMITED, wait_seconds=wait, bucket=bucket)
            return {
                "ok": False,
                "job": job.to_dict(),
                "stage_failed": "rate_limit",
                "wait_seconds": wait,
                "bucket": bucket,
                "stages_completed": stages_completed,
            }

        stages_completed.append("build_prompt")
        self.queue.update(job.job_id, JobStatus.PLANNED)

        render_result = self.provider.render(
            built,
            metadata={"job_id": job.job_id, "mode": self.pipeline_mode},
        )
        stages_completed.append("render")

        final_status = (
            JobStatus.DRY_RUN_COMPLETE
            if self.pipeline_mode == "dry_run"
            else JobStatus.PLANNED
        )
        self.queue.update(job.job_id, final_status, render=render_result)

        return {
            "ok": True,
            "job": self.queue.get(job.job_id).to_dict(),
            "render": render_result,
            "stages_completed": stages_completed,
            "rate_limit": self.rate_limiter.status(),
        }