"""
QuboCoin Wallet-CLI.
Die Balance lebt serverseitig im Pool-Ledger (ledger.py) und wird ausschliesslich
durch verifizierte PoW-Submissions erhoeht (siehe pool.py). Dieses Modul liest
nur die Identitaet (crypto_identity.py) und fragt den aktuellen Kontostand beim
Pool ab -- ein Client kann sich seine Balance nicht selbst gutschreiben.
"""
import requests
import config
from crypto_identity import MinerIdentity


def get_balance(pool_url: str = None) -> dict:
    pool_url = pool_url or config.POOL_HOST
    identity = MinerIdentity()
    resp = requests.get(f"{pool_url}/balance/{identity.address}", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {"address": identity.address, "balance": data.get("balance", 0.0)}


if __name__ == "__main__":
    info = get_balance()
    print(f"[WALLET] Adresse: {info['address']}")
    print(f"[WALLET] Bestaetigte Balance (vom Pool): {info['balance']} QBC")
