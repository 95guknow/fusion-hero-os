# -*- coding: utf-8 -*-
"""
bench.py  –  Schnell-Benchmark der Umgebung
Misst CPU, RAM, Disk, GPU (NVML), und QUBO-SA-Durchsatz.
"""
import time, os, math, random
from pathlib import Path

def banner(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

# ---------- CPU ----------
def bench_cpu():
    banner("CPU BENCHMARK")
    import psutil
    n = psutil.cpu_count()
    print(f"Logical cores: {n}")

    def cpu_work(seconds=1):
        start = time.perf_counter()
        x = 0
        while time.perf_counter() - start < seconds:
            for i in range(500_000):
                x += math.sqrt(i) * math.sin(i)
        return x

    t1 = time.perf_counter()
    cpu_work(1)
    t1 = time.perf_counter() - t1
    print(f"Single-core   : {1.0/max(t1,0.01):.1f} ops/s  ({t1:.3f}s for 1s work)")

    t2 = time.perf_counter()
    x = 0
    for _ in range(n):
        x += cpu_work(1)
    t2 = time.perf_counter() - t2
    print(f"Multi-core    : {n/max(t2,0.01):.1f} ops/s  ({t2:.3f}s total)")
    return {"cpu_cores": n, "cpu_single": round(1.0/max(t1,0.01),1), "cpu_multi": round(n/max(t2,0.01),1)}

# ---------- RAM ----------
def bench_ram():
    banner("RAM BENCHMARK")
    import psutil
    vm = psutil.virtual_memory()
    total_gb = round(vm.total / 1024**3, 1)
    print(f"Total         : {total_gb} GB")
    print(f"Used          : {vm.percent}%")
    # simple streaming write-read
    import tempfile
    size = 50 * 1024**2  # 50 MB
    tmp = tempfile.mktemp(suffix=".bin")
    data = os.urandom(1024*1024)
    t0 = time.perf_counter()
    with open(tmp, "wb") as f:
        for _ in range(50):
            f.write(data)
    tw = time.perf_counter() - t0
    t0 = time.perf_counter()
    with open(tmp, "rb") as f:
        while f.read(1024*1024):
            pass
    tr = time.perf_counter() - t0
    os.remove(tmp)
    print(f"Write 50 MB   : {50/max(tw,0.01):.0f} MB/s")
    print(f"Read  50 MB   : {50/max(tr,0.01):.0f} MB/s")
    return {"ram_total_gb": total_gb, "ram_write_mbs": round(50/max(tw,0.01)), "ram_read_mbs": round(50/max(tr,0.01))}

# ---------- DISK ----------
def bench_disk():
    banner("DISK BENCHMARK")
    import tempfile, psutil
    tmp = tempfile.mkdtemp(prefix="bench_disk_")
    size = 100 * 1024**2
    data = os.urandom(1024*1024)
    t0 = time.perf_counter()
    for i in range(100):
        with open(os.path.join(tmp, f"f{i}.bin"), "wb") as f:
            f.write(data)
    tw = time.perf_counter() - t0
    t0 = time.perf_counter()
    for i in range(100):
        with open(os.path.join(tmp, f"f{i}.bin"), "rb") as f:
            f.read()
    tr = time.perf_counter() - t0
    for i in range(100):
        os.remove(os.path.join(tmp, f"f{i}.bin"))
    os.rmdir(tmp)
    print(f"Write 100 MB  : {100/max(tw,0.01):.0f} MB/s")
    print(f"Read  100 MB  : {100/max(tr,0.01):.0f} MB/s")
    return {"disk_write_mbs": round(100/max(tw,0.01)), "disk_read_mbs": round(100/max(tr,0.01))}

# ---------- GPU (NVML) ----------
def bench_gpu():
    banner("GPU BENCHMARK")
    try:
        import pynvml
        pynvml.nvmlInit()
        h = pynvml.nvmlDeviceGetHandleByIndex(0)
        name = pynvml.nvmlDeviceGetName(h).decode()
        mem = pynvml.nvmlDeviceGetMemoryInfo(h)
        util = pynvml.nvmlDeviceGetUtilizationRates(h)
        temp = pynvml.nvmlDeviceGetTemperature(h, pynvml.NVML_TEMPERATURE_GPU)
        print(f"Device        : {name}")
        print(f"VRAM          : {mem.total//1024**2} MB  (used {mem.used//1024**2} MB)")
        print(f"Utilization   : GPU {util.gpu}%  MEM {util.memory}%")
        print(f"Temperature   : {temp} C")
        # simple fp32 throughput via small matmul test
        res = {"gpu_name": name, "gpu_vram_mb": mem.total//1024**2, "gpu_util": util.gpu, "gpu_temp": temp}
        try:
            import numpy as np
            n = 2048
            A = np.random.randn(n, n).astype(np.float32)
            B = np.random.randn(n, n).astype(np.float32)
            # warmup
            for _ in range(3):
                C = A @ B
            t0 = time.perf_counter()
            for _ in range(10):
                C = A @ B
            t = time.perf_counter() - t0
            flops = 10 * 2 * n**3
            print(f"FP32 Matmul   : {flops/max(t,0.01)/1e9:.1f} GFLOPS")
            res["gpu_gflops"] = round(flops/max(t,0.01)/1e9,1)
        except Exception as e:
            print(f"Matmul skipped : {e}")
        pynvml.nvmlShutdown()
        return res
    except Exception as e:
        print(f"NVML nicht verfuegbar / kein NVIDIA-GPU : {e}")
        return {"gpu_note": "n/a"}

# ---------- QUBO-SA throughput ----------
def bench_qubo():
    banner("QUBO-SA THROUGHPUT")
    import numpy as np
    random.seed(42)
    def energy(Q, v):
        n = len(Q)
        e = 0.0
        for i in range(n):
            for j in range(n):
                if Q[i][j]:
                    e += (0.5 if i==j else 1.0) * Q[i][j] * v[i] * v[j]
        return e

    def sa(Q, steps=2000):
        n = len(Q)
        x = [random.randint(0,1) for _ in range(n)]
        best_x, best_e = x[:], energy(Q,x)
        e = best_e
        for t in range(steps):
            T = 2.0*(1-t/steps)+1e-3
            i = random.randint(0,n-1)
            nx = x[:]; nx[i] = 1 - nx[i]
            ne = energy(Q,nx)
            if ne < e or random.random() < math.exp(-(ne-e)/T):
                x, e = nx, ne
                if e < best_e:
                    best_x, best_e = x[:], e
        return best_x

    sizes = [16, 32, 64]
    for n in sizes:
        Q = [[random.uniform(-1,1) for _ in range(n)] for _ in range(n)]
        t0 = time.perf_counter()
        runs = max(1, int(2000/max(n,1)))
        for _ in range(runs):
            _ = sa(Q, steps=1000)
        t = time.perf_counter() - t0
        print(f"n={n:3d}  {runs} SA-runs in {t:.2f}s  => {runs/max(t,0.01):.1f} runs/s")
    return {"qubo_note": "measured"}

# ---------- Main ----------
if __name__ == "__main__":
    cpu_r = bench_cpu()
    ram_r = bench_ram()
    dsk_r = bench_disk()
    gpu_r = bench_gpu()
    qubo_r = bench_qubo()

    banner("ZUSAMMENFASSUNG")
    all_r = {**cpu_r, **ram_r, **dsk_r, **gpu_r, **qubo_r}
    for k, v in all_r.items():
        print(f"{k:25s} : {v}")
    print("\nBenchmark beendet.")
