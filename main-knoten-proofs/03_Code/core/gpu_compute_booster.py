# gpu_compute_booster.py
# Echte GPU-Rechenlast (SM-Auslastung), nicht nur VRAM-Füllung.

from __future__ import annotations

import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

from gpu_memory_allocator import probe_gpu_memory

_LLAMA_PKG = (
    r"C:\Users\Admin\AppData\Local\Microsoft\WinGet\Packages"
    r"\ggml.llamacpp_Microsoft.Winget.Source_8wekyb3d8bbwe"
)


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass
class BoosterState:
    running: bool = False
    last_run: float = 0.0
    next_interval_s: float = 3.0
    last_action: str = "idle"
    target_compute_pct: float = 55.0
    last_compute_pct: float = 0.0
    batches_run: int = 0
    history: list = field(default_factory=list)


class GPUComputeBooster:
    """Führt CUDA-Workloads aus wenn GPU-SM-Auslastung unter Ziel liegt."""

    def __init__(self) -> None:
        self.target = _env_float("FUSION_GPU_COMPUTE_TARGET_PCT", 55.0)
        self.low_threshold = _env_float("FUSION_GPU_COMPUTE_LOW_PCT", 30.0)
        self.min_interval = _env_float("FUSION_GPU_BOOSTER_MIN_INTERVAL", 2.0)
        self.max_interval = _env_float("FUSION_GPU_BOOSTER_MAX_INTERVAL", 12.0)
        self.auto = os.getenv("FUSION_GPU_COMPUTE_BOOSTER_AUTO", "1").lower() in (
            "1", "true", "yes", "on",
        )
        self.state = BoosterState(target_compute_pct=self.target)
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._work_buffers: list = []
        self._server_proc: Optional[subprocess.Popen] = None
        self._server_port = _env_int("FUSION_LLAMA_SERVER_PORT", 8081)
        self._server_host = os.getenv("FUSION_LLAMA_SERVER_HOST", "127.0.0.1")
        self._boost_model = os.getenv(
            "FUSION_GPU_BOOST_MODEL",
            r"C:\Users\Admin\internal_llm\models\Llama-3.2-1B-Instruct-Q4_K_M.gguf",
        )
        self._gpu_layers = _env_int("FUSION_LLAMA_GPU_LAYERS", 99)
        self._ctx_size = _env_int("FUSION_LLAMA_CTX_SIZE", 512)
        self._ram_soft = _env_float("FUSION_RAM_SOFT_PCT", 80.0)

    def stop_server(self) -> bool:
        stopped = False
        if self._server_proc and self._server_proc.poll() is None:
            self._server_proc.terminate()
            try:
                self._server_proc.wait(timeout=5)
            except Exception:
                self._server_proc.kill()
            stopped = True
        self._server_proc = None
        return stopped

    def _server_base(self) -> str:
        return f"http://{self._server_host}:{self._server_port}"

    def _server_healthy(self) -> bool:
        try:
            import httpx
            r = httpx.get(f"{self._server_base()}/health", timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False

    def _ensure_llama_server(self) -> bool:
        import psutil
        if psutil.virtual_memory().percent >= self._ram_soft:
            self.state.last_action = "llama_server_skipped_ram_pressure"
            return False
        if self._server_healthy():
            return True
        if self._server_proc and self._server_proc.poll() is None:
            time.sleep(2.0)
            return self._server_healthy()
        model = Path(self._boost_model)
        if not model.exists():
            return False
        server = Path(os.getenv("LLAMA_SERVER_PATH", Path(_LLAMA_PKG) / "llama-server.exe"))
        if not server.exists():
            return False
        self._server_proc = subprocess.Popen(
            [
                str(server),
                "-m", str(model),
                "--port", str(self._server_port),
                "--host", self._server_host,
                "-ngl", str(self._gpu_layers),
                "-c", str(self._ctx_size),
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        deadline = time.time() + 45.0
        while time.time() < deadline:
            if self._server_healthy():
                return True
            time.sleep(1.0)
        return False

    def _run_llama_server_burst(self, tokens: int) -> Dict[str, Any]:
        if not self._ensure_llama_server():
            return {"ok": False, "error": "llama-server unavailable"}
        try:
            import httpx
            payload = {
                "prompt": "GPU boost",
                "n_predict": max(4, min(tokens, 32)),
                "temperature": 0.7,
            }
            start = time.perf_counter()
            r = httpx.post(
                f"{self._server_base()}/completion",
                json=payload,
                timeout=30.0,
            )
            latency_ms = round((time.perf_counter() - start) * 1000, 1)
            return {
                "ok": r.status_code == 200,
                "backend": "llama-server",
                "tokens": payload["n_predict"],
                "latency_ms": latency_ms,
                "http_status": r.status_code,
            }
        except Exception as exc:
            return {"ok": False, "backend": "llama-server", "error": str(exc)}

    def _run_llama_bench_burst(self, repetitions: int) -> Dict[str, Any]:
        model = Path(self._boost_model)
        bench = Path(os.getenv("LLAMA_BENCH_PATH", Path(_LLAMA_PKG) / "llama-bench.exe"))
        if not model.exists() or not bench.exists():
            return {"ok": False, "error": "llama-bench or model missing"}
        try:
            start = time.perf_counter()
            subprocess.run(
                [
                    str(bench), "-m", str(model),
                    "-ngl", str(self._gpu_layers),
                    "-r", str(max(1, repetitions)),
                    "--no-warmup", "-o", "json",
                ],
                capture_output=True,
                timeout=120,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            return {
                "ok": True,
                "backend": "llama-bench",
                "repetitions": repetitions,
                "latency_ms": round((time.perf_counter() - start) * 1000, 1),
            }
        except Exception as exc:
            return {"ok": False, "backend": "llama-bench", "error": str(exc)}

    def _ensure_buffers(self, intensity: int) -> None:
        try:
            import torch
            if not torch.cuda.is_available():
                return
            need = min(4, max(1, intensity))
            while len(self._work_buffers) < need:
                n = 512 + 256 * len(self._work_buffers)
                a = torch.randn(n, n, device="cuda", dtype=torch.float32)
                b = torch.randn(n, n, device="cuda", dtype=torch.float32)
                self._work_buffers.append((a, b))
        except Exception:
            pass

    def _run_cuda_batches(self, batches: int) -> Dict[str, Any]:
        batches = max(1, min(batches, 8))
        tokens = 8 + batches * 4

        if os.getenv("FUSION_LLAMA_SERVER_AUTO", "1").lower() in ("1", "true", "yes", "on"):
            burst = self._run_llama_server_burst(tokens)
            if burst.get("ok"):
                return {"batches": batches, **burst}

        bench = self._run_llama_bench_burst(max(1, batches // 2))
        if bench.get("ok"):
            return {"batches": batches, **bench}

        try:
            import torch
            if torch.cuda.is_available():
                self._ensure_buffers(batches)
                torch.cuda.synchronize()
                for a, b in self._work_buffers[:batches]:
                    c = torch.matmul(a, b)
                    c = torch.nn.functional.relu(c)
                    _ = c.sum()
                torch.cuda.synchronize()
                return {"batches": batches, "backend": "torch", "ok": True}
        except Exception:
            pass

        return {"batches": 0, "backend": None, "ok": False}

    def boost_once(self) -> Dict[str, Any]:
        with self._lock:
            snap = probe_gpu_memory()
            compute = snap.compute_util_pct
            vram = snap.dedicated_util_pct
            gap = max(0.0, self.target - compute)
            action = "hold"
            work: Dict[str, Any] = {}

            import psutil
            if psutil.virtual_memory().percent >= self._ram_soft:
                action = "boost_skipped_ram_pressure"
            elif snap.cuda_available and compute < self.low_threshold:
                intensity = int(1 + gap / 10.0)
                if compute < 15.0:
                    intensity = min(8, intensity + 2)
                work = self._run_cuda_batches(intensity)
                action = f"boost_compute_{intensity}x"
                self.state.batches_run += work.get("batches", 0)
            elif compute >= self.target:
                action = "compute_at_target"

            self.state.last_action = action
            self.state.last_compute_pct = compute
            self.state.last_run = time.time()

            if gap >= 20:
                self.state.next_interval_s = self.min_interval
            elif gap >= 8:
                self.state.next_interval_s = min(self.max_interval, self.min_interval * 2)
            else:
                self.state.next_interval_s = min(
                    self.max_interval, self.state.next_interval_s * 1.1,
                )

            entry = {
                "ts": self.state.last_run,
                "action": action,
                "compute_pct": compute,
                "vram_pct": vram,
                "target_pct": self.target,
                "gap": round(gap, 1),
                "work": work,
            }
            self.state.history.append(entry)
            self.state.history = self.state.history[-50:]

            return {
                "status": "ok",
                "action": action,
                "compute_util_pct": compute,
                "vram_util_pct": vram,
                "target_compute_pct": self.target,
                "work": work,
                "next_interval_s": self.state.next_interval_s,
            }

    def status(self) -> Dict[str, Any]:
        snap = probe_gpu_memory()
        with self._lock:
            return {
                "booster": {
                    "auto_enabled": self.auto,
                    "running": self.state.running,
                    "last_action": self.state.last_action,
                    "target_compute_pct": self.target,
                    "low_threshold_pct": self.low_threshold,
                    "last_compute_pct": self.state.last_compute_pct,
                    "batches_run": self.state.batches_run,
                    "next_interval_s": round(self.state.next_interval_s, 2),
                },
                "gpu": snap.to_dict(),
            }

    def _loop(self) -> None:
        self.state.running = True
        while not self._stop.is_set():
            try:
                self.boost_once()
            except Exception as exc:
                self.state.last_action = f"error:{exc}"
            self._stop.wait(self.state.next_interval_s)
        self.state.running = False

    def start_background(self) -> bool:
        if self._thread and self._thread.is_alive():
            return False
        if not self.auto:
            return False
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._loop, name="fusion-gpu-compute-booster", daemon=True,
        )
        self._thread.start()
        return True

    def stop_background(self) -> None:
        self._stop.set()


_booster: Optional[GPUComputeBooster] = None


def get_gpu_compute_booster() -> GPUComputeBooster:
    global _booster
    if _booster is None:
        _booster = GPUComputeBooster()
    return _booster