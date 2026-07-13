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

    print(f"[MINER] Starte QuboCoin-Miner gegen {pool_url}")
    print(f"[MINER] Cache path: {get_qubo_cache_path()}")
    print(f"[MINER] Belohnungs-Adresse: {miner.identity.address}")

    while True:
        try:
            resp = requests.get(f"{pool_url}/get_problem", timeout=10)
            problem = resp.json()

            print(f"Mining Problem: {problem['problem_id']} | Difficulty: {problem['difficulty']} "
                  f"| PoW-Bits: {problem.get('target_bits')}")

            result = miner.mine(
                problem_id=problem["problem_id"],
                Q=problem["Q"],
                bias=problem["bias"],
                difficulty=problem["difficulty"]
            )

            if result.get("pow_failed"):
                print(f"→ PoW nicht in max_tries gefunden (zu schwer) | Energy: {result['energy']:.4f} "
                      f"| Zeit: {result['time']}s. Naechstes Problem...")
                continue

            gpu_flag = " [GPU]" if result.get("used_gpu") else ""
            vht_flag = " [VHT]" if miner.vht_cache else ""
            print(f"→ Loesung + PoW gefunden! Energy: {result['energy']:.4f} | Nonce: {result['nonce']} "
                  f"| Zeit: {result['time']}s | mult={result.get('opt_mult',20):.1f}{gpu_flag}{vht_flag}")

            submit_resp = requests.post(f"{pool_url}/submit_solution", json=result, timeout=10)
            ack = submit_resp.json()

            if ack.get("status") == "accepted":
                print(f"   ✓ Pool: Block #{ack['block_index']} akzeptiert | Balance: {ack['balance']:.2f} QBC")
            else:
                print(f"   ✗ Pool hat abgelehnt: {ack.get('reason')}")

            pause = 0.3 if result.get("used_gpu") else 0.5
            time.sleep(pause)

        except Exception as e:
            print(f"Fehler: {e}")
            time.sleep(5)


if __name__ == "__main__":
    run_miner()
