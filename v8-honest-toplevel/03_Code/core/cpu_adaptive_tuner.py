# cpu_adaptive_tuner.py
# Adaptives CPU-Tuning: Taktung/Worker an Last + Temperatur koppeln.

from __future__ import annotations

import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import psutil


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, str(default)))
    except ValueError:
        return default


def probe_cpu() -> Dict[str, Any]:
    """CPU-Auslastung, Frequenz und Temperatur (falls verfügbar)."""
    load = psutil.cpu_percent(interval=0.5)
    per_cpu = psutil.cpu_percent(interval=0.3, percpu=True)
    freq = psutil.cpu_freq()
    temp_c: Optional[float] = None

    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
                if key in temps and temps[key]:
                    temp_c = max(t.current for t in temps[key] if t.current)
                    break
    except Exception:
        pass

    if temp_c is None:
        try:
            result = subprocess.run(
                [
                    "powershell", "-NoProfile", "-Command",
                    "(Get-CimInstance MSAcpi_ThermalZoneTemperature -Namespace root/wmi "
                    "| Select-Object -First 1).CurrentTemperature",
                ],
                capture_output=True,
                text=True,
                timeout=6,
            )
            if result.returncode == 0 and result.stdout.strip().isdigit():
                kelvin_tenth = int(result.stdout.strip())
                temp_c = (kelvin_tenth / 10.0) - 273.15
        except Exception:
            pass

    return {
        "load_pct": round(load, 1),
        "load_per_core": [round(x, 1) for x in per_cpu],
        "logical_cpus": psutil.cpu_count(logical=True) or 12,
        "physical_cpus": psutil.cpu_count(logical=False) or 6,
        "freq_mhz": round(freq.current, 0) if freq else None,
        "freq_max_mhz": round(freq.max, 0) if freq else None,
        "temp_c": round(temp_c, 1) if temp_c is not None else None,
    }


@dataclass
class CPUTunerState:
    running: bool = False
    performance_ratio: float = 0.67
    target_workers: int = 24
    last_action: str = "idle"
    last_run: float = 0.0
    next_interval_s: float = 5.0
    history: list = field(default_factory=list)


class CPUAdaptiveTuner:
    """
    Regeln (adaptiv):
    - Last < 50 % und Temp < 75 °C  → Leistung hoch (mehr Worker, höheres Ratio)
    - Last > 85 % oder Temp > 82 °C → drosseln
    - Sonst: halten
    """

    def __init__(self) -> None:
        self.temp_soft = _env_float("FUSION_CPU_TEMP_SOFT_C", 75.0)
        self.temp_hard = _env_float("FUSION_CPU_TEMP_HARD_C", 82.0)
        self.load_low = _env_float("FUSION_CPU_LOAD_LOW_PCT", 50.0)
        self.load_high = _env_float("FUSION_CPU_LOAD_HIGH_PCT", 85.0)
        self.min_interval = _env_float("FUSION_CPU_TUNER_MIN_INTERVAL", 3.0)
        self.max_interval = _env_float("FUSION_CPU_TUNER_MAX_INTERVAL", 20.0)
        self.auto = os.getenv("FUSION_CPU_TUNER_AUTO", "1").lower() in ("1", "true", "yes", "on")
        self.state = CPUTunerState()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()

    def status(self) -> Dict[str, Any]:
        snap = probe_cpu()
        with self._lock:
            return {
                "tuner": {
                    "auto_enabled": self.auto,
                    "running": self.state.running,
                    "performance_ratio": self.state.performance_ratio,
                    "target_workers": self.state.target_workers,
                    "last_action": self.state.last_action,
                    "next_interval_s": round(self.state.next_interval_s, 2),
                    "thresholds": {
                        "load_low_pct": self.load_low,
                        "load_high_pct": self.load_high,
                        "temp_soft_c": self.temp_soft,
                        "temp_hard_c": self.temp_hard,
                    },
                },
                "cpu": snap,
            }

    def _apply_hyperthreading(self, ratio: float, workers: int) -> None:
        os.environ["FUSION_PERFORMANCE_RATIO"] = str(round(ratio, 3))
        os.environ["FUSION_PROFILE"] = "admin" if ratio >= 0.85 else "balanced"
        try:
            import hyperthreading_config as ht
            ht.enable(True)
            if hasattr(ht, "_workers"):
                ht._workers = workers
        except Exception:
            pass

    def tune_once(self) -> Dict[str, Any]:
        with self._lock:
            snap = probe_cpu()
            load = snap["load_pct"]
            temp = snap.get("temp_c")
            cpus = snap["logical_cpus"]
            ratio = self.state.performance_ratio
            workers = self.state.target_workers
            action = "hold"

            temp_ok = temp is None or temp < self.temp_soft
            temp_hot = temp is not None and temp >= self.temp_hard
            temp_warm = temp is not None and temp >= self.temp_soft

            if load < self.load_low and temp_ok:
                ratio = min(1.0, ratio + 0.08)
                workers = min(cpus * 8, workers + cpus)
                action = "boost_cpu_underutilized"
            elif load > self.load_high or temp_hot:
                ratio = max(0.5, ratio - 0.1)
                workers = max(cpus, workers - cpus)
                action = "throttle_load_or_temp"
            elif temp_warm and load > 60:
                ratio = max(0.6, ratio - 0.05)
                workers = max(cpus * 2, workers - cpus // 2)
                action = "trim_warm"

            self.state.performance_ratio = round(ratio, 3)
            self.state.target_workers = int(workers)
            self.state.last_action = action
            self.state.last_run = time.time()

            self._apply_hyperthreading(ratio, workers)

            if os.getenv("FUSION_RESOURCE_COUPLER_AUTO", "1").lower() in ("1", "true", "yes", "on"):
                try:
                    from resource_coupler import get_resource_coupler
                    coupler = get_resource_coupler()
                    if not coupler.state.running:
                        snap_gpu = __import__(
                            "gpu_memory_allocator", fromlist=["probe_gpu_memory"],
                        ).probe_gpu_memory()
                        if snap_gpu.system_ram_util_pct >= 80.0 or (
                            temp_hot or load > self.load_high
                        ):
                            coupler.couple_once()
                except Exception:
                    pass

            prev_load = self.state.history[-1]["load_pct"] if self.state.history else load
            delta = abs(load - prev_load)
            if delta >= 15:
                self.state.next_interval_s = self.min_interval
            elif delta >= 5:
                self.state.next_interval_s = min(self.max_interval, self.min_interval * 2)
            else:
                self.state.next_interval_s = min(self.max_interval, self.state.next_interval_s * 1.2)

            entry = {
                "ts": self.state.last_run,
                "load_pct": load,
                "temp_c": temp,
                "ratio": ratio,
                "workers": workers,
                "action": action,
            }
            self.state.history.append(entry)
            self.state.history = self.state.history[-50:]

            return {"status": "ok", "action": action, "cpu": snap, "tuning": entry}

    def _loop(self) -> None:
        self.state.running = True
        while not self._stop.is_set():
            try:
                self.tune_once()
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
        self._thread = threading.Thread(target=self._loop, name="fusion-cpu-tuner", daemon=True)
        self._thread.start()
        return True

    def stop_background(self) -> None:
        self._stop.set()


_tuner: Optional[CPUAdaptiveTuner] = None


def get_cpu_tuner() -> CPUAdaptiveTuner:
    global _tuner
    if _tuner is None:
        _tuner = CPUAdaptiveTuner()
    return _tuner