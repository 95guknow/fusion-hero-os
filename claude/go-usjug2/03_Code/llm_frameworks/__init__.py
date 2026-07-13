# -*- coding: utf-8 -*-
"""Fusion Hero OS v8 — LLM Frameworks (je Provider ein eigenes Modul)."""
from .base import FrameworkResult, ROLE_SYSTEM, extract_json
from .registry import (
    TRINITY_LLMS,
    all_status,
    connector_status,
    filter_llm_pool,
    get_framework,
    invoke,
    list_frameworks,
    normalize_provider,
    pick_thinker_model,
    pick_verifier_model,
)

__all__ = [
    "FrameworkResult",
    "ROLE_SYSTEM",
    "TRINITY_LLMS",
    "all_status",
    "connector_status",
    "extract_json",
    "filter_llm_pool",
    "get_framework",
    "invoke",
    "list_frameworks",
    "normalize_provider",
    "pick_thinker_model",
    "pick_verifier_model",
]