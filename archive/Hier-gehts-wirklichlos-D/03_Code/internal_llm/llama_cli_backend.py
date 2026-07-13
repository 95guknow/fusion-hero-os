"""Llama.cpp CLI Backend — Fallback wenn llama-cpp-python illegal instruction wirft."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional

LLAMA_CLI = os.getenv(
    "LLAMA_CLI_PATH",
    r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages"
    r"\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe\llama-cli.exe",
)


def _default_gpu_layers() -> int:
    try:
        return int(os.getenv("FUSION_LLAMA_GPU_LAYERS", "20"))
    except ValueError:
        return 20


def generate(
    model_path: str,
    prompt: str,
    params: Dict[str, float],
    max_tokens: int = 128,
    n_gpu_layers: Optional[int] = None,
) -> str:
    if n_gpu_layers is None:
        n_gpu_layers = 0 if os.getenv("FUSION_HOST_RAM_MINIMAL") != "1" else _default_gpu_layers()
        if os.getenv("FUSION_OFFLOAD_TO_GPU") == "1":
            n_gpu_layers = _default_gpu_layers()
    cli = Path(LLAMA_CLI)
    if not cli.exists():
        raise FileNotFoundError(f"llama-cli nicht gefunden: {cli}")

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as f:
        f.write(prompt)
        prompt_file = f.name

    try:
        cmd = [
            str(cli),
            "-m", model_path,
            "-f", prompt_file,
            "-n", str(max_tokens),
            "--temp", str(params.get("temperature", 0.7)),
            "--top-p", str(params.get("top_p", 0.9)),
            "--repeat-penalty", str(params.get("repeat_penalty", 1.1)),
            "-ngl", str(n_gpu_layers),
            "--no-display-prompt",
            "-no-cnv",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, encoding="utf-8", errors="replace")
        if result.returncode != 0:
            raise RuntimeError(result.stderr[:500] or result.stdout[:500])
        text = result.stdout.strip()
        # llama-cli gibt oft prompt + generation zurück
        if prompt in text:
            text = text.split(prompt, 1)[-1].strip()
        return text
    finally:
        Path(prompt_file).unlink(missing_ok=True)