import hashlib
import time
from qubo_solver import QUBOSolver, deserialize_qubo
from optimizer import SelfOptimizer
from blockchain import target_from_difficulty, hash_meets_target
from crypto_identity import MinerIdentity


class QUBOMiner:
    def __init__(self, solver_type="neal"):
        self.solver = QUBOSolver(solver_type)
        self.stats = {"solutions_found": 0, "total_time": 0, "gpu_uses": 0, "pow_failures": 0}
        self.optimizer = SelfOptimizer()  # autonomous self-optimization
        self.vht_cache = None  # will be set for vhyperthreading
        self.identity = MinerIdentity()  # echtes ECDSA-Schluesselpaar fuer Rewards
        print(f"[MINER] Identity geladen. Adresse: {self.identity.address}")

    def _search_nonce(self, problem_id: str, proof: str, target_bits: int, max_tries: int = 5_000_000):
        """Echtes Hashcash-Proof-of-Work (wie Bitcoin): suche eine Nonce, sodass
        sha256(problem_id:proof:nonce) die geforderten Leading-Zero-Bits hat."""
        nonce = 0
        while nonce < max_tries:
            message = f"{problem_id}:{proof}:{nonce}"
            digest = hashlib.sha256(message.encode()).hexdigest()
            if hash_meets_target(digest, target_bits):
                return nonce, digest
            nonce += 1
        return None, None

    def mine(self, problem_id: str, Q: dict, bias: dict, difficulty: int):
        start = time.time()

        # Deserialize from pool
        Q_native, bias_native = deserialize_qubo(Q, bias)
        n = len(bias_native) if bias_native else len(Q_native)

        # Autonomous: decide strategy and params
        use_gpu = self.optimizer.should_prefer_gpu() and self.solver.solver_name != "neal"
        gpu_params = self.optimizer.get_gpu_params() if use_gpu else {}
        num_reads = self.optimizer.get_adaptive_num_reads(difficulty, n)

        # Pass problem_id for bcache/VRAM
        self.solver._current_problem_id = problem_id

        # vhyperthread support
        if self.vht_cache and use_gpu:
            self.solver.vht_cache = self.vht_cache

        # Solve with adaptive effort + cache
        if use_gpu:
            self.stats["gpu_uses"] += 1
            result = self.solver.solve(Q_native, bias_native, num_reads=num_reads,
                                       problem_id=problem_id, use_vram_cache=True,
                                       **gpu_params)
        else:
            result = self.solver.solve(Q_native, bias_native, num_reads=num_reads, problem_id=problem_id)

        # Proof: Hash der gefundenen Loesung
        solution_str = str(sorted(result["solution"].items()))
        proof = hashlib.sha256(solution_str.encode()).hexdigest()

        # Echtes Hashcash-PoW auf proof+nonce, Schwierigkeit kommt vom Pool
        target_bits = target_from_difficulty(difficulty)
        nonce, pow_hash = self._search_nonce(problem_id, proof, target_bits)

        elapsed = time.time() - start
        self.stats["solutions_found"] += 1
        self.stats["total_time"] += elapsed

        sol = {int(k): int(v) for k, v in result["solution"].items()}
        energy = float(result["energy"])

        # Feed back to self-optimizer (the key for autonomous weiter optimieren)
        used_gpu = "gpu" in str(result.get("num_reads", ""))
        self.optimizer.record_solve(n, elapsed, energy, used_gpu or use_gpu, difficulty)

        if self.optimizer and hasattr(self.optimizer, 'evolve_if_needed'):
            self.optimizer.evolve_if_needed()

        current_params = self.optimizer.get_current_params() if hasattr(self.optimizer, 'get_current_params') else self.optimizer.params

        if nonce is None:
            self.stats["pow_failures"] += 1
            return {
                "problem_id": problem_id,
                "pow_failed": True,
                "energy": energy,
                "time": round(elapsed, 3),
            }

        message = f"{problem_id}:{proof}:{nonce}"
        signature = self.identity.sign(message)

        return {
            "problem_id": problem_id,
            "solution": sol,
            "energy": energy,
            "proof": proof,
            "nonce": nonce,
            "pow_hash": pow_hash,
            "target_bits": target_bits,
            "pubkey": self.identity.pubkey_hex(),
            "address": self.identity.address,
            "signature": signature,
            "time": round(elapsed, 3),
            "difficulty": difficulty,
            "used_gpu": use_gpu,
            "opt_mult": current_params.get("num_reads_mult", 20),
        }
