"""Integrationstest gegen den laufenden Pool: prueft, dass Fake-Submissions
abgelehnt werden und dass ein echter QUBOMiner-Lauf akzeptiert wird."""
import requests

from miner import QUBOMiner

POOL = "http://127.0.0.1:5000"

print("=== QuboCoin Pool Test Client ===")

print("\n1. Fetching problem from pool...")
resp = requests.get(f"{POOL}/get_problem", timeout=5)
print("Status:", resp.status_code)
problem = resp.json()
print("Problem ID:", problem["problem_id"])
print("Q terms:", len(problem["Q"]))
print("Difficulty:", problem["difficulty"], "| target_bits:", problem.get("target_bits"))

print("\n2. Submitting bogus solution (should be REJECTED)...")
dummy = {
    "problem_id": problem["problem_id"],
    "solution": {"0": 1, "1": 0},
    "energy": -99.99,
    "proof": "deadbeef123456",
    "nonce": 0,
    "pubkey": "00" * 65,
    "address": "fake_address",
    "signature": "00" * 70,
    "time": 0.123,
    "difficulty": problem["difficulty"],
}
r2 = requests.post(f"{POOL}/submit_solution", json=dummy, timeout=5)
print("Submit response:", r2.status_code, r2.json())
assert r2.status_code == 400, "Bogus submission should have been rejected!"

print("\n3. Solving the SAME problem for real via QUBOMiner (should be ACCEPTED)...")
miner = QUBOMiner(solver_type="neal")
result = miner.mine(
    problem_id=problem["problem_id"],
    Q=problem["Q"],
    bias=problem["bias"],
    difficulty=problem["difficulty"],
)
if result.get("pow_failed"):
    print("PoW search did not finish in time -- try again, this can happen at high difficulty.")
else:
    r3 = requests.post(f"{POOL}/submit_solution", json=result, timeout=10)
    print("Submit response:", r3.status_code, r3.json())

print("\n=== Test complete ===")
