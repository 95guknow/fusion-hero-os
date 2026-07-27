"""
Hyperclusterup Zitterpolymesh — fluid workflow scheduler with
Parallel-Virtual-Hyperthreading (PVHT) across four lanes: CPU, MEM, GPU, QPU.

Semantik (ehrlich, keine Magie):

* PVHT = pro Lane ein eigener Worker-Pool mit Oversubscription-Faktor.
  Tasks fließen, sobald ihre Dependencies erfüllt sind — kein globaler
  Phasen-Barrier, dadurch "flüssige" Workflows.
* GPU-Lane ist nur dann ``virtual=False``, wenn echte Hardware erkannt wird
  (torch.cuda oder nvidia-smi). Sonst rechnet sie als virtuelle Lane auf CPU.
* QPU-Lane ist IMMER ``virtual=True``: sie nutzt dwave-neal (Simulated
  Annealing) falls installiert, sonst einen stdlib-SA-Fallback. Ein echter
  Quantenprozessor ist nicht angebunden; das Reporting sagt das explizit.
* Zitterfunktion = gedämpfter, begrenzter Jitter-Backoff bei Retries. Die
  Amplitude klingt pro Versuch ab, der Scheduler kehrt zum Fixpunkt
  (Basis-Delay) zurück — analog identity-fixpoint.md.

Nur Stdlib als harte Dependency; yaml/torch/neal werden optional erkannt.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import random
import shutil
import sys
import tempfile
import threading
import time
import hashlib
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
from collections.abc import Callable, Iterable, Sequence

__all__ = [
    "LaneKind",
    "LaneProfile",
    "ZitterJitter",
    "ZitterTask",
    "ZitterPolyMesh",
    "detect_lanes",
    "builtin_ops",
    "load_pipeline",
    "DEFAULT_PIPELINE_FILE",
]

DEFAULT_PIPELINE_FILE = "zitterpolymesh_pipeline.yaml"


class LaneKind(str, Enum):
    CPU = "cpu"
    MEM = "mem"
    GPU = "gpu"
    QPU = "qpu"


@dataclass(frozen=True)
class LaneProfile:
    kind: LaneKind
    workers: int
    backend: str
    virtual: bool
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind.value,
            "workers": self.workers,
            "backend": self.backend,
            "virtual": self.virtual,
            "detail": self.detail,
        }


def _pvht_factor(default: float = 2.0) -> float:
    try:
        return max(1.0, float(os.environ.get("FUSION_PVHT_FACTOR", default)))
    except ValueError:
        return default


def detect_lanes() -> dict[LaneKind, LaneProfile]:
    """Probe der vier Lanes. GPU/QPU werden ehrlich als virtuell markiert,
    wenn keine echte Hardware/Bibliothek vorhanden ist."""
    cores = os.cpu_count() or 2
    factor = _pvht_factor()
    lanes: dict[LaneKind, LaneProfile] = {}

    lanes[LaneKind.CPU] = LaneProfile(
        kind=LaneKind.CPU,
        workers=max(2, int(cores * factor)),
        backend="threadpool",
        virtual=False,
        detail=f"{cores} cores x PVHT-Faktor {factor:g}",
    )
    lanes[LaneKind.MEM] = LaneProfile(
        kind=LaneKind.MEM,
        workers=max(2, min(8, cores)),
        backend="threadpool-io",
        virtual=False,
        detail="I/O-gebundene Lane (Autosave, Shards, Archiv)",
    )

    gpu_backend, gpu_virtual, gpu_detail = "cpu-fallback", True, "keine GPU erkannt"
    try:  # pragma: no cover - hardwareabhängig
        import torch  # type: ignore

        if torch.cuda.is_available():
            gpu_backend = "torch-cuda"
            gpu_virtual = False
            gpu_detail = torch.cuda.get_device_name(0)
    except Exception:
        if shutil.which("nvidia-smi"):
            gpu_backend = "nvidia-smi-present"
            gpu_virtual = False
            gpu_detail = "GPU sichtbar, torch nicht installiert"
    lanes[LaneKind.GPU] = LaneProfile(
        kind=LaneKind.GPU,
        workers=2 if gpu_virtual else 4,
        backend=gpu_backend,
        virtual=gpu_virtual,
        detail=gpu_detail,
    )

    qpu_backend, qpu_detail = "stdlib-sa", "Simulated Annealing (Stdlib-Fallback)"
    try:
        import neal  # type: ignore  # noqa: F401

        qpu_backend = "dwave-neal"
        qpu_detail = "Simulated-Annealing-Sampler (Simulator, kein echter QPU)"
    except Exception:
        pass  # neal ist optional — Fallback bleibt der Stdlib-SA-Sampler
    lanes[LaneKind.QPU] = LaneProfile(
        kind=LaneKind.QPU,
        workers=2,
        backend=qpu_backend,
        virtual=True,  # ehrlich: immer Simulation
        detail=qpu_detail,
    )
    return lanes


# ---------------------------------------------------------------------------
# Zitterfunktion — gedämpfter, begrenzter Jitter-Backoff mit Fixpunkt
# ---------------------------------------------------------------------------


@dataclass
class ZitterJitter:
    """Delay(attempt) = base * growth^attempt * (1 ± amplitude * damping^attempt).

    Die Zitter-Amplitude klingt pro Versuch ab (Dämpfung), das Delay bleibt
    durch ``ceiling`` begrenzt — das System kehrt zum Fixpunkt zurück statt
    aufzuschwingen (Poly-Mesh-Zitterfunktion, siehe identity-fixpoint.md).
    """

    base: float = 0.05
    growth: float = 2.0
    amplitude: float = 0.5
    damping: float = 0.5
    ceiling: float = 2.0
    _rng: random.Random = field(default_factory=lambda: random.Random(0x5EED))

    def delay(self, attempt: int) -> float:
        raw = self.base * (self.growth ** attempt)
        amp = self.amplitude * (self.damping ** attempt)
        jittered = raw * (1.0 + self._rng.uniform(-amp, amp))
        return max(0.0, min(self.ceiling, jittered))


# ---------------------------------------------------------------------------
# Tasks + Mesh
# ---------------------------------------------------------------------------

TaskFn = Callable[[dict[str, Any]], Any]


@dataclass
class ZitterTask:
    name: str
    lane: LaneKind
    fn: TaskFn
    deps: tuple[str, ...] = ()
    retries: int = 2
    payload: dict[str, Any] = field(default_factory=dict)


class MeshValidationError(ValueError):
    pass


class ZitterPolyMesh:
    """DAG-Scheduler: pro Lane ein Pool, Tasks starten sofort bei erfüllten
    Dependencies (fluid), Retries mit gedämpftem Zitter-Backoff."""

    def __init__(
        self,
        lanes: dict[LaneKind, LaneProfile] | None = None,
        jitter: ZitterJitter | None = None,
    ):
        self.lanes = lanes or detect_lanes()
        self.jitter = jitter or ZitterJitter()
        self._tasks: dict[str, ZitterTask] = {}

    def add_task(
        self,
        name: str,
        lane: LaneKind | str,
        fn: TaskFn,
        deps: Sequence[str] = (),
        retries: int = 2,
        payload: dict[str, Any] | None = None,
    ) -> ZitterPolyMesh:
        if name in self._tasks:
            raise MeshValidationError(f"Task doppelt definiert: {name}")
        self._tasks[name] = ZitterTask(
            name=name,
            lane=LaneKind(lane),
            fn=fn,
            deps=tuple(deps),
            retries=retries,
            payload=dict(payload or {}),
        )
        return self

    # -- Validierung -------------------------------------------------------

    def validate(self) -> list[str]:
        """Prüft unbekannte Dependencies, unbekannte Lanes und Zyklen (Kahn).
        Gibt die topologische Reihenfolge zurück; wirft MeshValidationError."""
        for t in self._tasks.values():
            for dep in t.deps:
                if dep not in self._tasks:
                    raise MeshValidationError(
                        f"Task '{t.name}' referenziert unbekannte Dependency '{dep}'"
                    )
            if t.lane not in self.lanes:
                raise MeshValidationError(f"Task '{t.name}' nutzt unbekannte Lane '{t.lane}'")

        indegree = {name: len(t.deps) for name, t in self._tasks.items()}
        dependents: dict[str, list[str]] = {name: [] for name in self._tasks}
        for t in self._tasks.values():
            for dep in t.deps:
                dependents[dep].append(t.name)

        queue = sorted(n for n, d in indegree.items() if d == 0)
        order: list[str] = []
        while queue:
            node = queue.pop(0)
            order.append(node)
            for nxt in dependents[node]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)
            queue.sort()
        if len(order) != len(self._tasks):
            cyclic = sorted(set(self._tasks) - set(order))
            raise MeshValidationError(f"Zyklus im Mesh: {cyclic}")
        return order

    # -- Ausführung --------------------------------------------------------

    def run(self, timeout: float = 300.0) -> dict[str, Any]:
        self.validate()
        t_start = time.perf_counter()

        executors = {
            kind: concurrent.futures.ThreadPoolExecutor(
                max_workers=profile.workers,
                thread_name_prefix=f"zpm-{kind.value}",
            )
            for kind, profile in self.lanes.items()
        }

        cond = threading.Condition()
        results: dict[str, dict[str, Any]] = {}
        remaining_deps = {name: set(t.deps) for name, t in self._tasks.items()}
        dependents: dict[str, list[str]] = {name: [] for name in self._tasks}
        for t in self._tasks.values():
            for dep in t.deps:
                dependents[dep].append(t.name)
        submitted: set = set()

        def _run_task(task: ZitterTask) -> None:
            record: dict[str, Any] = {
                "lane": task.lane.value,
                "attempts": 0,
                "status": "failed",
                "error": None,
                "result": None,
            }
            started = time.perf_counter()
            ctx = {
                "payload": task.payload,
                "deps": {d: results[d].get("result") for d in task.deps},
                "lane": self.lanes[task.lane].as_dict(),
            }
            for attempt in range(task.retries + 1):
                record["attempts"] = attempt + 1
                try:
                    record["result"] = task.fn(ctx)
                    record["status"] = "ok"
                    record["error"] = None
                    break
                except Exception as exc:  # noqa: BLE001
                    record["error"] = f"{type(exc).__name__}: {exc}"
                    if attempt < task.retries:
                        time.sleep(self.jitter.delay(attempt))
            record["duration_sec"] = round(time.perf_counter() - started, 4)
            with cond:
                results[task.name] = record
                _release_dependents(task.name, record["status"] == "ok")
                cond.notify_all()

        def _skip(name: str, reason: str) -> None:
            results[name] = {
                "lane": self._tasks[name].lane.value,
                "attempts": 0,
                "status": "skipped",
                "error": reason,
                "result": None,
                "duration_sec": 0.0,
            }
            _release_dependents(name, ok=False)

        def _release_dependents(name: str, ok: bool) -> None:
            # unter cond-Lock aufgerufen
            for nxt in dependents[name]:
                if not ok:
                    if nxt not in results and nxt not in submitted:
                        _skip(nxt, f"Dependency '{name}' fehlgeschlagen/übersprungen")
                    continue
                remaining_deps[nxt].discard(name)
                if not remaining_deps[nxt] and nxt not in submitted and nxt not in results:
                    _submit(nxt)

        def _submit(name: str) -> None:
            submitted.add(name)
            task = self._tasks[name]
            executors[task.lane].submit(_run_task, task)

        with cond:
            for name, deps in remaining_deps.items():
                if not deps:
                    _submit(name)
            deadline = time.monotonic() + timeout
            while len(results) < len(self._tasks):
                slack = deadline - time.monotonic()
                if slack <= 0 or not cond.wait(timeout=min(slack, 1.0)):
                    if time.monotonic() >= deadline:
                        for name in set(self._tasks) - set(results):
                            _skip(name, "Mesh-Timeout")
                        break

        for ex in executors.values():
            ex.shutdown(wait=True, cancel_futures=True)

        lane_stats: dict[str, dict[str, Any]] = {}
        for kind, profile in self.lanes.items():
            lane_tasks = [r for r in results.values() if r["lane"] == kind.value]
            lane_stats[kind.value] = {
                **profile.as_dict(),
                "tasks": len(lane_tasks),
                "ok": sum(1 for r in lane_tasks if r["status"] == "ok"),
                "busy_sec": round(sum(r.get("duration_sec", 0.0) for r in lane_tasks), 4),
            }

        wall = time.perf_counter() - t_start
        busy_total = sum(s["busy_sec"] for s in lane_stats.values())
        return {
            "ok": all(r["status"] == "ok" for r in results.values()),
            "tasks": results,
            "lanes": lane_stats,
            "wall_sec": round(wall, 4),
            "busy_sec_total": round(busy_total, 4),
            # >1.0 nur bei echter Parallelität über Lanes/Worker hinweg
            "parallel_speedup": round(busy_total / wall, 3) if wall > 0 else 0.0,
        }


# ---------------------------------------------------------------------------
# Builtin-Ops für Smoke-Tests (echte, verifizierbare Arbeit pro Lane)
# ---------------------------------------------------------------------------


def _op_cpu_sum_squares(ctx: dict[str, Any]) -> dict[str, Any]:
    n = int(ctx["payload"].get("n", 200_000))
    total = sum(i * i for i in range(n))
    expected = (n - 1) * n * (2 * n - 1) // 6
    if total != expected:
        raise RuntimeError("CPU-Selbsttest fehlgeschlagen")
    return {"n": n, "sum_squares": total}


def _op_mem_shard_roundtrip(ctx: dict[str, Any]) -> dict[str, Any]:
    size = int(ctx["payload"].get("bytes", 1_000_000))
    blob = os.urandom(size)
    digest = hashlib.sha256(blob).hexdigest()
    with tempfile.NamedTemporaryFile(delete=False) as fh:
        fh.write(blob)
        tmp = fh.name
    try:
        read_back = Path(tmp).read_bytes()
    finally:
        os.unlink(tmp)
    if hashlib.sha256(read_back).hexdigest() != digest:
        raise RuntimeError("MEM-Roundtrip: Checksumme weicht ab")
    return {"bytes": size, "sha256": digest}


def _op_gpu_matmul(ctx: dict[str, Any]) -> dict[str, Any]:
    n = int(ctx["payload"].get("n", 64))
    lane = ctx.get("lane", {})
    if lane.get("backend") == "torch-cuda":  # pragma: no cover - hardwareabhängig
        import torch  # type: ignore

        a = torch.ones((n, n), device="cuda")
        c = (a @ a).sum().item()
        backend = "torch-cuda"
    else:
        row = [1.0] * n
        c = sum(sum(row) for _ in range(n)) * n  # (A@A).sum für A=1: n^3
        backend = "cpu-fallback"
    expected = float(n) ** 3
    if abs(c - expected) > 1e-6 * expected:
        raise RuntimeError(f"GPU-Matmul-Selbsttest: {c} != {expected}")
    return {"n": n, "checksum": c, "backend": backend, "virtual": backend != "torch-cuda"}


def _solve_qubo_stdlib(q: dict[tuple[int, int], float], n_vars: int, sweeps: int = 400) -> tuple[list[int], float]:
    rng = random.Random(42)

    def energy(x: list[int]) -> float:
        return sum(coeff * x[i] * x[j] for (i, j), coeff in q.items())

    x = [rng.randint(0, 1) for _ in range(n_vars)]
    best, best_e = list(x), energy(x)
    for sweep in range(sweeps):
        temp = max(0.01, 2.0 * (1.0 - sweep / sweeps))
        i = rng.randrange(n_vars)
        x[i] ^= 1
        e = energy(x)
        if e <= best_e or rng.random() < pow(2.718281828, -(e - best_e) / temp):
            if e < best_e:
                best, best_e = list(x), e
        else:
            x[i] ^= 1
    return best, best_e


def _op_qpu_min_qubo(ctx: dict[str, Any]) -> dict[str, Any]:
    # Kleines QUBO mit bekanntem Optimum: x0=x1=1, x2=0 → Energie -3
    q = {(0, 0): -2.0, (1, 1): -2.0, (2, 2): 1.0, (0, 1): 1.0, (1, 2): 2.0}
    backend = ctx.get("lane", {}).get("backend", "stdlib-sa")
    if backend == "dwave-neal":
        try:
            import neal  # type: ignore

            sampler = neal.SimulatedAnnealingSampler()
            sampleset = sampler.sample_qubo(q, num_reads=32)
            best = sampleset.first
            bits = [int(best.sample[i]) for i in range(3)]
            energy = float(best.energy)
        except Exception:
            bits, energy = _solve_qubo_stdlib(q, 3)
            backend = "stdlib-sa"
    else:
        bits, energy = _solve_qubo_stdlib(q, 3)
    if energy > -3.0 + 1e-9:
        raise RuntimeError(f"QPU-Annealer fand Optimum nicht: E={energy}")
    return {"bits": bits, "energy": energy, "backend": backend, "virtual": True}


def builtin_ops() -> dict[str, TaskFn]:
    return {
        "cpu_sum_squares": _op_cpu_sum_squares,
        "mem_shard_roundtrip": _op_mem_shard_roundtrip,
        "gpu_matmul": _op_gpu_matmul,
        "qpu_min_qubo": _op_qpu_min_qubo,
    }


# ---------------------------------------------------------------------------
# Pipeline-Loader (YAML wenn verfügbar, sonst JSON)
# ---------------------------------------------------------------------------


def load_pipeline(path: os.PathLike | str) -> dict[str, Any]:
    text = Path(path).read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except ImportError:
        data = json.loads(text)
    if not isinstance(data, dict) or "workflows" not in data:
        raise MeshValidationError(f"Pipeline-Datei ohne 'workflows'-Block: {path}")
    return data


def mesh_from_pipeline(
    pipeline: dict[str, Any],
    workflow: str,
    ops: dict[str, TaskFn] | None = None,
    lanes: dict[LaneKind, LaneProfile] | None = None,
) -> ZitterPolyMesh:
    ops = ops or builtin_ops()
    workflows = pipeline.get("workflows") or {}
    if workflow not in workflows:
        raise MeshValidationError(
            f"Workflow '{workflow}' nicht in Pipeline (vorhanden: {sorted(workflows)})"
        )
    mesh = ZitterPolyMesh(lanes=lanes)
    for spec in workflows[workflow].get("tasks", []):
        op_name = spec.get("op")
        if op_name not in ops:
            raise MeshValidationError(f"Unbekannte Op '{op_name}' in Task '{spec.get('name')}'")
        mesh.add_task(
            name=spec["name"],
            lane=spec.get("lane", "cpu"),
            fn=ops[op_name],
            deps=spec.get("deps", []),
            retries=int(spec.get("retries", 2)),
            payload=spec.get("payload") or {},
        )
    return mesh


# ---------------------------------------------------------------------------
# CLI — von CI-Workflows genutzt
# ---------------------------------------------------------------------------


def _cli(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Hyperclusterup Zitterpolymesh")
    parser.add_argument("--probe", action="store_true", help="Lane-Profile als JSON ausgeben")
    parser.add_argument("--validate", action="store_true", help="Pipeline-DAG validieren")
    parser.add_argument("--smoke", action="store_true", help="Smoke-Op einer Lane ausführen")
    parser.add_argument("--lane", choices=[k.value for k in LaneKind], default="cpu")
    parser.add_argument("--run", metavar="WORKFLOW", help="Workflow aus Pipeline ausführen")
    parser.add_argument("--pipeline", default=DEFAULT_PIPELINE_FILE)
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.probe:
        lanes = {k.value: p.as_dict() for k, p in detect_lanes().items()}
        print(json.dumps(lanes, indent=2, ensure_ascii=False))
        return 0

    if args.validate:
        pipeline = load_pipeline(args.pipeline)
        for wf_name in pipeline.get("workflows", {}):
            order = mesh_from_pipeline(pipeline, wf_name).validate()
            print(f"workflow '{wf_name}': ok ({len(order)} Tasks, Reihenfolge {order})")
        return 0

    if args.smoke:
        lane = LaneKind(args.lane)
        smoke_op = {
            LaneKind.CPU: "cpu_sum_squares",
            LaneKind.MEM: "mem_shard_roundtrip",
            LaneKind.GPU: "gpu_matmul",
            LaneKind.QPU: "qpu_min_qubo",
        }[lane]
        mesh = ZitterPolyMesh()
        mesh.add_task(f"smoke-{lane.value}", lane, builtin_ops()[smoke_op])
        report = mesh.run(timeout=120.0)
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["ok"] else 1

    if args.run:
        pipeline = load_pipeline(args.pipeline)
        mesh = mesh_from_pipeline(pipeline, args.run)
        report = mesh.run(timeout=float(pipeline.get("timeout_sec", 300)))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0 if report["ok"] else 1

    parser.print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(_cli())
