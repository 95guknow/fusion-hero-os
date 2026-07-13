"""
Echte kryptographische Identitaet fuer den QUBO-Coin.
ECDSA (SECP256K1, dieselbe Kurve wie Bitcoin) ueber die Python `cryptography`-Bibliothek.
Erzeugt ein echtes Schluesselpaar, leitet eine Adresse ab und signiert/verifiziert
Mining-Submissions, damit der Pool Rewards eindeutig einem Miner zuordnen kann.
"""
import os
import hashlib
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature, decode_dss_signature
from cryptography.exceptions import InvalidSignature

KEY_DIR = r"C:\FusionHero\QuboCache"
PRIVATE_KEY_FILE = os.path.join(KEY_DIR, "miner_identity.pem")


def _public_bytes(public_key) -> bytes:
    return public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )


def address_from_pubkey_bytes(pub_bytes: bytes) -> str:
    """Adresse = sha256(sha256(pubkey)) hex, kurz (analog Bitcoin-Hash160-Idee, vereinfacht)."""
    h = hashlib.sha256(hashlib.sha256(pub_bytes).digest()).hexdigest()
    return "qbc1" + h[:40]


class MinerIdentity:
    """Persistentes ECDSA-Schluesselpaar fuer diesen Miner."""

    def __init__(self, key_path: str = PRIVATE_KEY_FILE):
        self.key_path = key_path
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        self.private_key = self._load_or_create()
        self.public_key = self.private_key.public_key()
        self.pub_bytes = _public_bytes(self.public_key)
        self.address = address_from_pubkey_bytes(self.pub_bytes)

    def _load_or_create(self):
        if os.path.exists(self.key_path):
            with open(self.key_path, "rb") as f:
                return serialization.load_pem_private_key(f.read(), password=None)
        key = ec.generate_private_key(ec.SECP256K1())
        pem = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
        with open(self.key_path, "wb") as f:
            f.write(pem)
        print(f"[IDENTITY] Neues Schluesselpaar erzeugt: {self.key_path}")
        return key

    def sign(self, message: str) -> str:
        sig = self.private_key.sign(message.encode(), ec.ECDSA(hashes.SHA256()))
        return sig.hex()

    def pubkey_hex(self) -> str:
        return self.pub_bytes.hex()


def verify_signature(pubkey_hex: str, message: str, signature_hex: str) -> bool:
    try:
        pub_bytes = bytes.fromhex(pubkey_hex)
        public_key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256K1(), pub_bytes)
        signature = bytes.fromhex(signature_hex)
        public_key.verify(signature, message.encode(), ec.ECDSA(hashes.SHA256()))
        return True
    except (InvalidSignature, ValueError, Exception):
        return False


def address_from_pubkey_hex(pubkey_hex: str) -> str:
    return address_from_pubkey_bytes(bytes.fromhex(pubkey_hex))


if __name__ == "__main__":
    identity = MinerIdentity()
    print("Address:", identity.address)
    msg = "hello-pow"
    sig = identity.sign(msg)
    ok = verify_signature(identity.pubkey_hex(), msg, sig)
    print("Signature valid:", ok)
    print("Address re-derived matches:", address_from_pubkey_hex(identity.pubkey_hex()) == identity.address)
