"""Unified data models for Fusion Hero OS v8.4 Core.

Central place for Task, LLMResult (re-export), TaskResult etc.
Prevents scattered dicts and makes the whole system type-safe and testable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Re-export the canonical LLMResult so existing code can import from one place
try:
    from ..providers.base import LLMResult  # type: ignore
except Exception:  # fallback if providers not yet loaded
    from dataclasses import dataclass, field
    from typing import Any, Dict, List, Optional

    @dataclass
    class LLMResult:  # type: ignore
        provider: str
        response: str
        latency_ms: float = 0.0
        fallback_chain: List[str] = field(default_factory=list)
        meta: Dict[str, Any] = field(default_factory=dict)
        success: bool = True
        error: Optional[str] = None


@dataclass
class Task:
    """Generic task object passed to Orchestrator / Dispatcher."""
    id: str
    query: str
    intent: Optional[str] = None
    system_prompt: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskResult:
    """Result returned by Orchestrator after processing a Task."""
    success: bool = True
    output: str = ""
    provider: Optional[str] = None
    latency_ms: float = 0.0
    fallback_chain: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
