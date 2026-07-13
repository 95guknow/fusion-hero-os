import dimod
import neal
import time
from typing import Dict, Tuple, Optional, Any

from cache_integration import CacheManager

def deserialize_qubo(q_serial: dict, bias_serial: dict):
    """Wandelt vom Pool empfangene serialisierte Q/Bias (String-Keys) in native Form zurück."""
    Q = {}
    for k, v in q_serial.items():
        if isinstance(k, str) and "," in k:
            i, j = map(int, k.split(","))
            Q[(i, j)] = float(v)
        else:
            # Fallback falls schon Tuple
            Q[k] = float(v)
    bias = {int(k): float(v) for k, v in bias_serial.items()}
    return Q, bias

class QUBOSolver:
    def __init__(self, solver: str = "neal"):
        self.solver_name = solver
        if solver == "neal":
            self.sampler = neal.SimulatedAnnealingSampler()
        elif solver == "gpu":
            self.sampler = None
        else:
            self.sampler = None  # custom later
        self.cache = CacheManager()

    def solve(self, Q: Dict[Tuple[int, int], float], bias: Dict[int, float], 
              num_reads: int = 1000, problem_id: str = None, use_vram_cache: bool = True,
              pop_size=None, generations=None, mutation_rate=None, elite_size=None) -> Dict:
        """Löst eine QUBO-Instanz mit bcache + VRAM Cache Support."""
        if problem_id:
            cached = self.cache.load_solution(problem_id)
            if cached:
                print(f"[Cache] Treffer für {problem_id}")
                return cached

        if self.solver_name == "gpu":
            result = self.solve_with_gpu_hook(Q, bias, num_reads, 
                                              pop_size=pop_size, generations=generations,
                                              mutation_rate=mutation_rate, elite_size=elite_size)
        else:
            # Merge bias into Q as diagonal for proper QUBO (Neal)
            Q_full = dict(Q)
            for i, b in bias.items():
                key = (i, i) if (i, i) in Q_full else (i, i)
                Q_full[key] = Q_full.get(key, 0.0) + b

            bqm = dimod.BinaryQuadraticModel.from_qubo(Q_full)

            if self.solver_name == "neal" and self.sampler is not None:
                response = self.sampler.sample(bqm, num_reads=num_reads)
            else:
                temp_sampler = neal.SimulatedAnnealingSampler()
                response = temp_sampler.sample(bqm, num_reads=num_reads)

            best = response.first
            result = {
                "solution": {int(k): int(v) for k, v in best.sample.items()},
                "energy": float(best.energy),
                "num_reads": num_reads
            }

        if problem_id:
            self.cache.save_solution(problem_id, result)
            self.cache.save_problem(problem_id, Q, bias)

        return result

    def solve_with_gpu_hook(self, Q, bias, num_reads=1000, pop_size=None, generations=None, mutation_rate=None, elite_size=None):
        """GPU-beschleunigter evolutionary Solver mit Selektion + Mutation (Cupy GA-style) + VRAM + bcache.
        Besser als reiner Random Search. Autonom anpassbar."""
        try:
            import cupy as cp
            # Determine n
            n = 4
            all_indices = set()
            for k in list(Q.keys()) + list(bias.keys()):
                if isinstance(k, (tuple, list)):
                    all_indices.update(int(x) for x in k)
                elif isinstance(k, str) and "," in k:
                    all_indices.update(int(x) for x in k.split(","))
                elif isinstance(k, (int, str)):
                    try:
                        all_indices.add(int(k))
                    except:
                        pass
            if all_indices:
                n = max(all_indices) + 1
            n = max(n, 4)

            # VRAM preload using CacheManager
            problem_id = getattr(self, '_current_problem_id', None)
            if problem_id:
                vram = self.cache.preload_to_vram(problem_id, Q, bias, n)
                Qmat = vram["Q"]
                bvec = vram["bias"]
            else:
                Qmat = cp.zeros((n, n), dtype=cp.float32)
                for k, val in Q.items():
                    if isinstance(k, (tuple, list)) and len(k) == 2:
                        i, j = int(k[0]), int(k[1])
                        Qmat[i, j] = val
                        Qmat[j, i] = val
                    elif isinstance(k, str) and "," in k:
                        i, j = map(int, k.split(","))
                        Qmat[i, j] = val
                        Qmat[j, i] = val
                bvec = cp.zeros(n, dtype=cp.float32)
                for i, v in bias.items():
                    bvec[int(i)] = float(v)

            # Warm-start: use previous best solution from cache as seed for population (self-optimization)
            initial_pop = None
            if problem_id:
                prev = self.cache.load_solution(problem_id)
                if prev and "solution" in prev:
                    try:
                        seed = cp.array([prev["solution"].get(i, 0) for i in range(n)], dtype=cp.float32)
                        initial_pop = cp.tile(seed, (pop_size, 1))
                        # add some mutation to seed
                        mut = cp.random.random((pop_size, n)) < 0.1
                        initial_pop = cp.where(mut, 1 - initial_pop, initial_pop)
                    except:
                        pass

            # Use adaptive or default GA params (self-optimization will pass better ones)
            pop_size = pop_size or 512
            generations = generations or 120
            mutation_rate = mutation_rate or 0.08
            elite_size = elite_size or 8

            vht = getattr(self, 'vht_cache', None)
            use_vht = vht and vht._use() and len(vht._streams) > 1

            if use_vht:
                # VHyperthread capable: run several virtual GA "threads" in parallel using different CUDA streams
                # Allocate virtual threads
                num_vthreads = min(8, len(vht._streams))  # use up to 8 virtual threads
                v_tids = []
                for _ in range(num_vthreads):
                    tid = vht.allocate_virtual_thread()
                    if tid > 0:
                        v_tids.append(tid)

                if not v_tids:
                    use_vht = False
                else:
                    print(f"[VHT] Using {len(v_tids)} virtual hyperthreads for parallel GA search (streams)")

            if not use_vht:
                if initial_pop is None:
                    pop = cp.random.randint(0, 2, size=(pop_size, n), dtype=cp.int32).astype(cp.float32)
                else:
                    pop = initial_pop

            def evaluate(p):
                quad = cp.einsum('bi,ij,bj->b', p, Qmat, p)
                lin = cp.einsum('bi,i->b', p, bvec)
                return quad + lin

            if use_vht:
                # Run parallel sub-GAs on different streams, collect best
                sub_size = max(64, pop_size // len(v_tids))
                sub_gens = max(20, generations // 2)
                best_overall_energy = float('inf')
                best_overall_sample = None

                for idx, tid in enumerate(v_tids):
                    stream = vht._streams[idx % len(vht._streams)]
                    with stream:
                        sub_pop = cp.random.randint(0, 2, size=(sub_size, n), dtype=cp.int32).astype(cp.float32)
                        for g in range(sub_gens):
                            energies = evaluate(sub_pop)
                            sidx = cp.argsort(energies)
                            elite = sub_pop[sidx[:elite_size]].copy()
                            new_p = elite.copy()
                            while len(new_p) < sub_size:
                                pidx = cp.random.choice(sub_size, 2, replace=False)
                                p1, p2 = sub_pop[pidx[0]], sub_pop[pidx[1]]
                                cpnt = cp.random.randint(1, n)
                                ch = cp.concatenate([p1[:cpnt], p2[cpnt:]])
                                mm = cp.random.random(n) < mutation_rate
                                ch = cp.where(mm, 1 - ch, ch)
                                new_p = cp.vstack([new_p, ch.reshape(1, -1)])
                            sub_pop = new_p[:sub_size]
                        fe = evaluate(sub_pop)
                        bi = int(cp.argmin(fe))
                        be = float(fe[bi].get())
                        if be < best_overall_energy:
                            best_overall_energy = be
                            best_overall_sample = sub_pop[bi].get().astype(int)

                sol_dict = {i: int(best_overall_sample[i]) for i in range(n)}
                print(f"[VHT+GPU-GA] Parallel vhyperthread search done. Best energy: {best_overall_energy:.4f} (using {len(v_tids)} vthreads)")
                return {"solution": sol_dict, "energy": best_overall_energy, "num_reads": pop_size * generations}
            else:
                # Original single GA path
                if initial_pop is None:
                    pop = cp.random.randint(0, 2, size=(pop_size, n), dtype=cp.int32).astype(cp.float32)
                else:
                    pop = initial_pop

                def evaluate(p):
                    quad = cp.einsum('bi,ij,bj->b', p, Qmat, p)
                    lin = cp.einsum('bi,i->b', p, bvec)
                    return quad + lin

                for gen in range(generations):
                    energies = evaluate(pop)
                    sorted_idx = cp.argsort(energies)
                    elite = pop[sorted_idx[:elite_size]].copy()
                    new_pop = elite.copy()
                    while len(new_pop) < pop_size:
                        parents_idx = cp.random.choice(pop_size, 2, replace=False)
                        p1, p2 = pop[parents_idx[0]], pop[parents_idx[1]]
                        cross_point = cp.random.randint(1, n)
                        child = cp.concatenate([p1[:cross_point], p2[cross_point:]])
                        mut_mask = cp.random.random(n) < mutation_rate
                        child = cp.where(mut_mask, 1 - child, child)
                        new_pop = cp.vstack([new_pop, child.reshape(1, -1)])
                    pop = new_pop[:pop_size]

                final_energies = evaluate(pop)
                best_idx = int(cp.argmin(final_energies))
                best_sample = pop[best_idx].get().astype(int)
                best_energy = float(final_energies[best_idx].get())

                sol_dict = {i: int(best_sample[i]) for i in range(n)}
                print(f"[GPU-GA] CuPy evolutionary done (pop={pop_size}, gen={generations}). Best energy: {best_energy:.4f}")
                return {"solution": sol_dict, "energy": best_energy, "num_reads": pop_size * generations}
        except Exception as e:
            print(f"[GPU-GA] CuPy evolutionary failed: {e}. Fallback to Neal.")
            neal_solver = QUBOSolver("neal")
            return neal_solver.solve(Q, bias, num_reads)
