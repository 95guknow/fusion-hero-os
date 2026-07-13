"""Schnelles Llama-Backend via llama-server HTTP (Port 8081)."""

from __future__ import annotations

import os
import time
from typing import Dict, Optional

import httpx

HOST = os.getenv("FUSION_LLAMA_SERVER_HOST", "127.0.0.1")
PORT = int(os.getenv("FUSION_LLAMA_SERVER_PORT", "8081"))


def _base() -> str:
    return f"http://{HOST}:{PORT}"


def healthy() -> bool:
    try:
        r = httpx.get(f"{_base()}/health", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def generate(
    prompt: str,
    params: Dict[str, float],
    max_tokens: int = 128,
) -> str:
    if not healthy():
        raise RuntimeError("llama-server nicht erreichbar auf :8081")
    payload = {
        "prompt": prompt,
        "n_predict": max_tokens,
        "temperature": params.get("temperature", 0.7),
        "top_p": params.get("top_p", 0.9),
        "repeat_penalty": params.get("repeat_penalty", 1.1),
    }
    r = httpx.post(f"{_base()}/completion", json=payload, timeout=60.0)
    r.raise_for_status()
    data = r.json()
    text = data.get("content", "") or data.get("response", "")
    if not text and "choices" in data:
        text = data["choices"][0].get("text", "")
    return str(text).strip()