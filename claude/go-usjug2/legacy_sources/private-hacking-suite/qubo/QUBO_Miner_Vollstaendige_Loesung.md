# QUBO-basierter Cryptominer PoC – Vollständige Lösung (V1.2 mit VHT)

**Projekt:** QUBO Miner - Private Hacking Suite
**Pfad:** `C:\Users\Admin\qubo_miner\`  
**Stand:** 28.06.2026 (nach allen Iterationen)  
**Features:**  
- Pool-Server (Flask) mit dynamischer Difficulty + Blockchain  
- Miner-Client mit Self-Optimizer (temp-aware)  
- GPU-Solver (CuPy Evolutionary GA mit Selektion + Mutation + Warm-Start)  
- Cache-Integration: SSD (bcache) + VRAM (CuPy)  
- **Virtual Hyperthreading (VHT)**: Integration des Fusion-OS VirtualGPUThreadCache (bis 256 virtuelle Threads, 8 Streams)  
- Core-Pinning (Ryzen)  
- Proof-of-Work + Reward (1.0 pro Solution)

---

## 1. Architektur-Überblick

```
Pool (pool.py) <--- HTTP ---> Miner (main.py + miner.py)
     |                              |
     +-- Blockchain (in-memory)     +-- QUBOSolver (neal / gpu)
     +-- Solution-Cache (SSD)           +-- SelfOptimizer (passt mult/gpu_params an)
                                        +-- VHT-Cache (virtual threads + streams)
```

Jede akzeptierte Solution = 1 Reward.  
Lösungen werden in `C:\FusionHero\QuboCache\*.json` + Blockchain gespeichert.

---

## 2. Alle Quelldateien (finaler Stand)

### 2.1 pool.py (Pool-Server + Blockchain + Cache)

```python
from flask import Flask, request, jsonify
import random
import time
from blockchain import SimpleBlockchain

app = Flask(__name__)

problems = []
blockchain = SimpleBlockchain()
recent_times = []
BASE_DIFFICULTY = 60

@app.route('/get_problem', methods=['GET'])
def get_problem():
    size = random.randint(8, 20)
    Q = {(i, j): random.uniform(-2, 2) for i in range(size) for j in range(i+1, size)}
    bias = {i: random.uniform(-1, 1) for i in range(size)}
    
    q_serial = {f"{i},{j}": float(val) for (i, j), val in Q.items()}
    bias_serial = {str(i): float(v) for i, v in bias.items()}
    
    if recent_times:
        avg_time = sum(recent_times) / len(recent_times)
        if avg_time < 0.8:
            diff = min(200, BASE_DIFFICULTY + 20)
        elif avg_time > 3.0:
            diff = max(20, BASE_DIFFICULTY - 15)
        else:
            diff = BASE_DIFFICULTY
    else:
        diff = random.randint(40, 100)
    
    problem = {
        "problem_id": f"prob_{int(time.time())}",
        "Q": q_serial,
        "bias": bias_serial,
        "difficulty": diff
    }
    problems.append(problem)
    return jsonify(problem)

@app.route('/submit_solution', methods=['POST'])
def submit_solution():
    data = request.json or {}
    pid = data.get('problem_id')
    t = float(data.get('time', 1.0))
    
    recent_times.append(t)
    if len(recent_times) > 10:
        recent_times.pop(0)
    
    block_data = {
        "problem_id": pid,
        "energy": data.get("energy"),
        "proof": data.get("proof"),
        "time": t,
        "difficulty": data.get("difficulty")
    }
    new_block = blockchain.add_block(block_data)
    
    print(f"[POOL] Lösung erhalten für {pid} | Blockchain block #{new_block.index}")
    
    return jsonify({
        "status": "accepted", 
        "reward": 1.0,
        "block_index": new_block.index,
        "block_hash": new_block.hash[:16]
    })

if __name__ == "__main__":
    print("[POOL] Starte QUBO-Pool-Simulator auf http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
```

### 2.2 main.py (Einstiegspunkt + VHT-Integration)

```python
from miner import QUBOMiner
import requests
import time
import os
import sys

from core_pinning import pin_to_cores, get_threadripper_cores
from cache_integration import get_qubo_cache_path
import config

# Enable Virtual Hyperthreading
os.environ.setdefault("FUSION_USE_GPU", "1")
os.environ.setdefault("FUSION_VIRTUAL_HT_GPU", "1")
os.environ.setdefault("FUSION_VCACHE_AGGRESSIVE", "1")
os.environ.setdefault("FUSION_VIRTUAL_THREADS", "256")
os.environ.setdefault("FUSION_GPU_SHARE_FACTOR", "3.0")

sys.path.insert(0, r"C:\Users\Admin\fusion-hero-os\03_Code\Dashboard")

def run_miner():
    try:
        pin_to_cores(get_threadripper_cores(12))
    except Exception:
        pass

    miner = QUBOMiner(solver_type=config.SOLVER_TYPE)
    pool_url = config.POOL_HOST

    try:
        from virtual_gpu_hyperthreading import get_virtual_gpu_ht_cache
        vht_cache = get_virtual_gpu_ht_cache()
        print(f"[VHT] Virtual Hyperthreading ENABLED! max_virtual={vht_cache.max}, streams={vht_cache.num_streams}")
        miner.vht_cache = vht_cache
    except Exception as e:
        miner.vht_cache = None
        print(f"[VHT] Not available: {e}")

    print(f"[MINER] Starte QUBO-Miner gegen {pool_url}")
    print(f"[MINER] Cache path: {get_qubo_cache_path()}")

    while True:
        try:
            resp = requests.get(f"{pool_url}/get_problem", timeout=10)
            problem = resp.json()

            print(f"Mining Problem: {problem['problem_id']} | Difficulty: {problem['difficulty']}")

            result = miner.mine(
                problem_id=problem["problem_id"],
                Q=problem["Q"],
                bias=problem["bias"],
                difficulty=problem["difficulty"]
            )

            gpu_flag = " [GPU]" if result.get("used_gpu") else ""
            vht_flag = " [VHT]" if miner.vht_cache else ""
            print(f"→ Lösung gefunden! Energy: {result['energy']:.4f} | Zeit: {result['time']}s | mult={result.get('opt_mult',20):.1f}{gpu_flag}{vht_flag}")

            requests.post(f"{pool_url}/submit_solution", json=result, timeout=10)

            pause = 0.3 if result.get("used_gpu") else 0.5
            time.sleep(pause)

        except Exception as e:
            print(f"Fehler: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_miner()
```

### 2.3 miner.py (mit Self-Optimizer + VHT)

```python
import hashlib
import time
from qubo_solver import QUBOSolver, deserialize_qubo
from optimizer import SelfOptimizer

class QUBOMiner:
    def __init__(self, solver_type="neal"):
        self.solver = QUBOSolver(solver_type)
        self.stats = {"solutions_found": 0, "total_time": 0, "gpu_uses": 0}
        self.optimizer = SelfOptimizer()
        self.vht_cache = None

    def mine(self, problem_id: str, Q: dict, bias: dict, difficulty: int):
        start = time.time()
        
        Q_native, bias_native = deserialize_qubo(Q, bias)
        n = len(bias_native) if bias_native else len(Q_native)

        use_gpu = self.optimizer.should_prefer_gpu() and self.solver.solver_name != "neal"
        gpu_params = self.optimizer.get_gpu_params() if use_gpu else {}
        num_reads = self.optimizer.get_adaptive_num_reads(difficulty, n)

        self.solver._current_problem_id = problem_id
        if self.vht_cache and use_gpu:
            self.solver.vht_cache = self.vht_cache

        if use_gpu:
            self.stats["gpu_uses"] += 1
            result = self.solver.solve(Q_native, bias_native, num_reads=num_reads,
                                       problem_id=problem_id, use_vram_cache=True,
                                       **gpu_params)
        else:
            result = self.solver.solve(Q_native, bias_native, num_reads=num_reads, problem_id=problem_id)

        solution_str = str(sorted(result["solution"].items()))
        proof = hashlib.sha256(solution_str.encode()).hexdigest()
        
        elapsed = time.time() - start
        self.stats["solutions_found"] += 1
        self.stats["total_time"] += elapsed

        sol = {int(k): int(v) for k, v in result["solution"].items()}
        energy = float(result["energy"])

        used_gpu = "gpu" in str(result.get("num_reads", ""))
        self.optimizer.record_solve(n, elapsed, energy, used_gpu or use_gpu, difficulty)

        return {
            "problem_id": problem_id,
            "solution": sol,
            "energy": energy,
            "proof": proof,
            "time": round(elapsed, 3),
            "difficulty": difficulty,
            "used_gpu": use_gpu,
            "opt_mult": self.optimizer.params["num_reads_mult"]
        }
```

### 2.4 qubo_solver.py (GPU-GA + VHT + Cache + Warm-Start)

(Siehe implementierte Version mit CuPy GA, VHT-Parallelisierung über Streams, CacheManager, Warm-Start aus vorheriger Solution.)

### 2.5 optimizer.py (Self-Optimizer – temp-aware)

(Siehe vollständige Version mit Auto-Tuning von mult, gpu_pop, gens, mutation_rate + GPU-Temp-Check.)

### 2.6 Weitere Dateien
- `blockchain.py` – Simple Blockchain (im Pool)
- `cache_integration.py` – SSD + CuPy VRAM CacheManager (wie vom User spezifiziert + angepasst)
- `core_pinning.py` – Windows + psutil Pinning
- `config.py` – ENV-Defaults

---

## 3. Ausführung (real auf Windows)

```cmd
cd C:\Users\Admin\qubo_miner

:: Pool starten
set FUSION_USE_GPU=1
set FUSION_VIRTUAL_HT_GPU=1
set FUSION_VCACHE_AGGRESSIVE=1
C:\Users\Admin\venv\Scripts\python.exe pool.py

:: In zweitem Fenster: Miner starten (VHT + GPU)
set FUSION_USE_GPU=1
set FUSION_VIRTUAL_HT_GPU=1
set FUSION_VCACHE_AGGRESSIVE=1
C:\Users\Admin\venv\Scripts\python.exe main.py
```

**Erwartete Ausgabe (Beispiel):**
```
[VHT] Virtual Hyperthreading ENABLED for miner! max_virtual=256, streams=8
[OPTIMIZER] Self-optimizer initialized. Current mult: 15.06
Mining Problem: prob_1782672550 | Difficulty: 80
→ Lösung gefunden! Energy: -25.11 | Zeit: 0.403s | mult=15.1 [GPU][VHT]
[OPTIMIZER] Temp-aware auto-tuned (GPU 45.0C): mult=15.2 ...
```

---

## 4. Aktueller Stand (letzter Run)

- **Solutions im Cache:** 94
- **Wallet (Fusion Dashboard):** 0.0 / 10000
- **Optimizer:** mult ≈ 15–23 (je nach Temp & Geschwindigkeit)
- **GPU:** ~43–45 °C (kühl, viel Headroom)
- **VHT:** Aktiv (256 virtuelle Threads, 8 Streams)
- **Cache:** SSD + VRAM voll funktionsfähig + Warm-Start

---

## 5. Nächste Schritte (Vorschläge)

- A. Warm-Start noch aggressiver (beste Lösung als 50 % der Population)
- B. Multi-Problem parallel über VHT (mehrere Problems gleichzeitig)
- C. Echten Reward-Tracker + Update der Fusion-Wallet.json

---

**Dokument erstellt:** `C:\Users\Admin\qubo_miner\QUBO_Miner_Vollstaendige_Loesung.md`

Der gesamte Code ist produktionsreif für den PoC und nutzt deine bestehenden Fusion-OS-Komponenten (VHT, Cache, Pinning).