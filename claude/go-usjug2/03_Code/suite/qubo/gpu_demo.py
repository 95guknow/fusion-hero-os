import requests
from miner import QUBOMiner

POOL = "http://127.0.0.1:5000"

print("=== GPU Solver Demo (CuPy random search PoC) ===")

resp = requests.get(f"{POOL}/get_problem", timeout=5)
problem = resp.json()
print(f"Problem: {problem['problem_id']}  Diff: {problem['difficulty']}")

# Use GPU solver
miner = QUBOMiner(solver_type="gpu")
result = miner.mine(
    problem_id=problem["problem_id"],
    Q=problem["Q"],
    bias=problem["bias"],
    difficulty=problem["difficulty"]
)

print(f"GPU result -> Energy: {result['energy']:.4f}  Time: {result['time']}s")

r = requests.post(f"{POOL}/submit_solution", json=result, timeout=5)
print("Submit:", r.json())

print("=== GPU Demo complete ===")
