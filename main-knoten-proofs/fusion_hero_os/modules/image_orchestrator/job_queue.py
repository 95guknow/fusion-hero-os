"""Job-Queue mit Status-Tracking für Bild-Pipeline."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class JobStatus(str, Enum):
    QUEUED = "queued"
    RATE_LIMITED = "rate_limited"
    PLANNED = "planned"
    DRY_RUN_COMPLETE = "dry_run_complete"
    FAILED = "failed"


@dataclass
class ImageJob:
    job_id: str
    prompt: str
    built_prompt: str
    status: JobStatus
    created_at: float = field(default_factory=time.time)
    wait_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "job_id": self.job_id,
            "prompt": self.prompt,
            "built_prompt": self.built_prompt,
            "status": self.status.value,
            "created_at": self.created_at,
            "wait_seconds": self.wait_seconds,
            "metadata": self.metadata,
        }


class ImageJobQueue:
    def __init__(self, max_history: int = 200) -> None:
        self._jobs: Dict[str, ImageJob] = {}
        self._order: List[str] = []
        self.max_history = max_history

    def create(self, prompt: str, built_prompt: str, **meta: Any) -> ImageJob:
        job_id = str(uuid.uuid4())[:8]
        job = ImageJob(
            job_id=job_id,
            prompt=prompt,
            built_prompt=built_prompt,
            status=JobStatus.QUEUED,
            metadata=meta,
        )
        self._jobs[job_id] = job
        self._order.append(job_id)
        self._trim()
        return job

    def update(self, job_id: str, status: JobStatus, **fields: Any) -> Optional[ImageJob]:
        job = self._jobs.get(job_id)
        if not job:
            return None
        job.status = status
        for k, v in fields.items():
            if hasattr(job, k):
                setattr(job, k, v)
            else:
                job.metadata[k] = v
        return job

    def get(self, job_id: str) -> Optional[ImageJob]:
        return self._jobs.get(job_id)

    def list_recent(self, n: int = 20) -> List[Dict[str, Any]]:
        ids = self._order[-n:]
        return [self._jobs[i].to_dict() for i in ids if i in self._jobs]

    def _trim(self) -> None:
        while len(self._order) > self.max_history:
            old = self._order.pop(0)
            self._jobs.pop(old, None)