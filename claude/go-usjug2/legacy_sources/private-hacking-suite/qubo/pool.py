"""
QuboCoin Pool-Server.
Hybrid Proof-of-Work:
  1) QUBO-Qualitaetsgate: die eingereichte Loesung wird vom Pool selbst aus dem
     gespeicherten Problem (Q, bias) nachgerechnet -> Cheating/Bluff wird erkannt.
  2) Echtes Hashcash-PoW (wie Bitcoin/Litecoin): sha256(problem_id:proof:nonce)
     muss die durch `difficulty` vorgegebene Anzahl Leading-Zero-Bits erfuellen.
  3) Echte ECDSA-Signatur: nur der Inhaber des Private Keys, der zur angegebenen
     Adresse gehoert, kann den Reward fuer diese Adresse einfordern.
Rewards werden serverseitig in einem persistenten Ledger gutgeschrieben (nicht
vom Client selbst), damit niemand sich Balance "einreden" kann.
"""
from flask import Flask, request, jsonify
import random
import time
import hashlib

from blockchain import SimpleBlockchain, target_from_difficulty, hash_meets_target
from ledger import Ledger
from crypto_identity import verify_signature, address_from_pubkey_hex

app = Flask(__name__)

problems = {}          # problem_id -> {Q, bias, difficulty, created}
PROBLEM_TTL = 600       # Sekunden, danach verfaellt ein Problem
MAX_PROBLEMS = 500

blockchain = SimpleBlockchain()
ledger = Ledger()
recent_times = []
BASE_DIFFICULTY = 60
REWARD = 1.0
MIN_QUALITY_FACTOR = -0.15  # geforderte Energie <= MIN_QUALITY_FACTOR * n (Anti-Trivial-Solution)


def _prune_problems():
    now = time.time()
    expired = [pid for pid, p in problems.items() if now - p["created"] > PROBLEM_TTL]
    for pid in expired:
        del problems[pid]
    if len(problems) > MAX_PROBLEMS:
        for pid in sorted(problems, key=lambda p: problems[p]["created"])[: len(problems) - MAX_PROBLEMS]:
            del problems[pid]


def _real_energy(Q: dict, bias: dict, solution: dict) -> float:
    """Berechnet die echte QUBO-Energie der eingereichten Loesung direkt aus
    dem beim Pool gespeicherten Problem -- unabhaengig von der Client-Angabe."""
    energy = 0.0
    for (i, j), val in Q.items():
        xi = solution.get(i, solution.get(str(i), 0))
        xj = solution.get(j, solution.get(str(j), 0))
        energy += val * int(xi) * int(xj)
    for i, val in bias.items():
        xi = solution.get(i, solution.get(str(i), 0))
        energy += val * int(xi)
    return energy


@app.route('/get_problem', methods=['GET'])
def get_problem():
    _prune_problems()
    size = random.randint(8, 20)
    Q = {(i, j): random.uniform(-2, 2) for i in range(size) for j in range(i + 1, size)}
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

    problem_id = f"prob_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    problems[problem_id] = {"Q": Q, "bias": bias, "n": size, "difficulty": diff, "created": time.time()}

    return jsonify({
        "problem_id": problem_id,
        "Q": q_serial,
        "bias": bias_serial,
        "difficulty": diff,
        "target_bits": target_from_difficulty(diff),
    })


@app.route('/submit_solution', methods=['POST'])
def submit_solution():
    data = request.json or {}
    pid = data.get('problem_id')
    nonce = data.get('nonce')
    proof = data.get('proof')
    pubkey = data.get('pubkey')
    address = data.get('address')
    signature = data.get('signature')
    solution = data.get('solution') or {}
    t = float(data.get('time', 1.0))

    problem = problems.get(pid)
    if not problem:
        return jsonify({"status": "rejected", "reason": "unknown_or_expired_problem_id"}), 400

    if not all([nonce is not None, proof, pubkey, address, signature]):
        return jsonify({"status": "rejected", "reason": "missing_fields"}), 400

    # 1) Identitaet: Adresse muss wirklich zum Public Key gehoeren, Signatur muss stimmen
    if address_from_pubkey_hex(pubkey) != address:
        return jsonify({"status": "rejected", "reason": "address_pubkey_mismatch"}), 400

    message = f"{pid}:{proof}:{nonce}"
    if not verify_signature(pubkey, message, signature):
        return jsonify({"status": "rejected", "reason": "invalid_signature"}), 400

    # 2) Proof muss wirklich der Hash der eingereichten Loesung sein
    solution_str = str(sorted(((int(k), int(v)) for k, v in solution.items())))
    expected_proof = hashlib.sha256(solution_str.encode()).hexdigest()
    if expected_proof != proof:
        return jsonify({"status": "rejected", "reason": "proof_mismatch"}), 400

    # 3) Hashcash-PoW: echte Rechenarbeit, serverseitig nachgerechnet
    target_bits = target_from_difficulty(problem["difficulty"])
    pow_hash = hashlib.sha256(message.encode()).hexdigest()
    if not hash_meets_target(pow_hash, target_bits):
        return jsonify({"status": "rejected", "reason": "pow_target_not_met", "target_bits": target_bits}), 400

    # 4) QUBO-Qualitaetsgate: Energie serverseitig aus dem Original-Problem nachrechnen
    sol_native = {int(k): int(v) for k, v in solution.items()}
    real_energy = _real_energy(problem["Q"], problem["bias"], sol_native)
    claimed_energy = float(data.get("energy", 0.0))
    if abs(real_energy - claimed_energy) > 1e-3:
        return jsonify({"status": "rejected", "reason": "energy_mismatch",
                         "claimed": claimed_energy, "real": real_energy}), 400

    quality_bound = MIN_QUALITY_FACTOR * problem["n"]
    if real_energy > quality_bound:
        return jsonify({"status": "rejected", "reason": "solution_quality_too_low",
                         "energy": real_energy, "required_max": quality_bound}), 400

    # Alles gueltig -> Block + Reward
    recent_times.append(t)
    if len(recent_times) > 10:
        recent_times.pop(0)

    block_data = {
        "problem_id": pid,
        "address": address,
        "energy": real_energy,
        "proof": proof,
        "nonce": nonce,
        "pow_hash": pow_hash,
        "time": t,
        "difficulty": problem["difficulty"],
        "reward": REWARD,
    }
    new_block = blockchain.add_block(block_data)
    new_balance = ledger.credit(address, REWARD)
    del problems[pid]

    print(f"[POOL] Block #{new_block.index} akzeptiert | {address[:14]}... | "
          f"Energy: {real_energy:.4f} | Balance: {new_balance:.2f}")

    return jsonify({
        "status": "accepted",
        "reward": REWARD,
        "balance": new_balance,
        "block_index": new_block.index,
        "block_hash": new_block.hash[:16],
    })


@app.route('/balance/<address>', methods=['GET'])
def get_balance(address):
    return jsonify({"address": address, "balance": ledger.get(address)})


@app.route('/chain', methods=['GET'])
def get_chain():
    n = int(request.args.get("last", 20))
    return jsonify({
        "length": len(blockchain.chain),
        "valid": blockchain.is_valid(),
        "blocks": [b.to_dict() for b in blockchain.chain[-n:]],
    })


@app.route('/stats', methods=['GET'])
def stats():
    return jsonify({
        "chain_length": len(blockchain.chain),
        "open_problems": len(problems),
        "total_addresses": len(ledger.balances),
        "total_paid": sum(ledger.balances.values()),
    })


if __name__ == "__main__":
    print("[POOL] Starte QuboCoin-Pool auf http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
