"""Persistentes Pool-Ledger: Adresse -> Balance. Die einzige Quelle der Wahrheit
fuer Kontostaende (nicht der Client!), damit ein Miner sich nicht selbst Reward
gutschreiben kann."""
import json
import os
import threading

LEDGER_FILE = r"C:\FusionHero\QuboCache\ledger.json"
_lock = threading.Lock()


class Ledger:
    def __init__(self, path: str = LEDGER_FILE):
        self.path = path
        self.balances = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    self.balances = json.load(f)
            except Exception:
                self.balances = {}

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self.balances, f, indent=2)

    def credit(self, address: str, amount: float) -> float:
        with _lock:
            self.balances[address] = self.balances.get(address, 0.0) + amount
            self._save()
            return self.balances[address]

    def get(self, address: str) -> float:
        return self.balances.get(address, 0.0)
