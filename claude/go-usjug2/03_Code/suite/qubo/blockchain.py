import time
import json
import os
import hashlib
from typing import List, Dict, Optional

CHAIN_FILE = r"C:\FusionHero\QuboCache\blockchain.json"


def target_from_difficulty(difficulty: int) -> int:
    """Wandelt 'difficulty' in eine Anzahl benoetigter Leading-Zero-Bits im Hash um.
    Echtes Hashcash-Prinzip wie bei Bitcoin/Litecoin etc.
    difficulty steigt -> mehr Nullbits -> exponentiell mehr Versuche noetig.
    Bits sind auf 6..20 begrenzt, damit ein CPU-Nonce-Search auf einem normalen
    Rechner Sekundenbruchteile bis wenige Sekunden dauert (echtes PoW, aber praxistauglich)."""
    return min(20, max(6, 6 + difficulty // 10))


def hash_meets_target(hex_digest: str, target_bits: int) -> bool:
    value = int(hex_digest, 16)
    total_bits = len(hex_digest) * 4
    return (value >> (total_bits - target_bits)) == 0


class Block:
    def __init__(self, index: int, timestamp: float, data: dict, previous_hash: str, hash_: Optional[str] = None):
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        self.hash = hash_ or self._calculate_hash()

    def _calculate_hash(self) -> str:
        block_string = f"{self.index}{self.timestamp}{json.dumps(self.data, sort_keys=True)}{self.previous_hash}"
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }

    @staticmethod
    def from_dict(d: dict) -> "Block":
        return Block(d["index"], d["timestamp"], d["data"], d["previous_hash"], d["hash"])


class SimpleBlockchain:
    def __init__(self, chain_file: str = CHAIN_FILE):
        self.chain_file = chain_file
        self.chain: List[Block] = []
        if not self._load():
            self._create_genesis_block()
            self._save()

    def _create_genesis_block(self):
        genesis = Block(0, time.time(), {"genesis": "QuboCoin PoC"}, "0")
        self.chain.append(genesis)

    def _load(self) -> bool:
        if not os.path.exists(self.chain_file):
            return False
        try:
            with open(self.chain_file, "r") as f:
                raw = json.load(f)
            chain = [Block.from_dict(b) for b in raw]
            if chain:
                self.chain = chain
                return True
        except Exception as e:
            print(f"[CHAIN] Laden fehlgeschlagen, starte neue Chain: {e}")
        return False

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.chain_file), exist_ok=True)
            with open(self.chain_file, "w") as f:
                json.dump([b.to_dict() for b in self.chain], f, indent=2)
        except Exception as e:
            print(f"[CHAIN] Speichern fehlgeschlagen: {e}")

    def add_block(self, data: dict) -> Block:
        previous_block = self.chain[-1]
        new_block = Block(len(self.chain), time.time(), data, previous_block.hash)
        self.chain.append(new_block)
        self._save()
        return new_block

    def is_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.hash != current._calculate_hash():
                return False
            if current.previous_hash != previous.hash:
                return False
        return True

    def get_latest(self) -> Block:
        return self.chain[-1]


if __name__ == "__main__":
    bc = SimpleBlockchain(chain_file=r"C:\FusionHero\QuboCache\blockchain_test.json")
    bc.add_block({"problem_id": "test", "reward": 1.0})
    print("Blockchain valid:", bc.is_valid())
    print("Latest block hash:", bc.get_latest().hash[:16] + "...")
    print("Chain length:", len(bc.chain))
