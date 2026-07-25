# -*- coding: utf-8 -*-
"""
AscensionOS - RootAnchorHandshake (v2.0, axiomatisch verankert)

Operationalisiert den im Gemini-Brainstorm vom 2026-07-24 vorgeschlagenen
"Layer 0 externer Host <-> SSH Hugging Handshake" als reine, netzwerklose
Ed25519 Sign/Verify-Primitive ueber ein kanonisches JSON-Manifest.

Axiom-Anker: proof_registry.yaml ROOT-ANCHOR-TAMPER-DETECT (BEWIESEN).

Ehrlicher Status:
  1. Dies ist eine echte, generische, OFFLINE Kryptographie-Primitive
     (Ed25519 via der bereits im Repo etablierten `cryptography`-Bibliothek;
     Praezedenz: src/normal_os/ascension/suite/qubo/crypto_identity.py mit
     ECDSA). Es wird KEIN SSH-Protokoll und KEIN Netzwerk-Handshake ueber
     eine Leitung implementiert — "Hugging Handshake" bleibt ein Bild aus
     dem Brainstorm, kein Transport-Layer.
  2. Dieses Modul ist NICHT mit einem bestehenden MasterSeed-/Foundation-
     Laufzeitobjekt verdrahtet. Es ist ein eigenstaendiger Baustein, der die
     brainstormte Idee ehrlich und konkret grundiert — keine Behauptung,
     dass "Layer 0 jetzt kryptographisch Layer 1 im laufenden System
     verifiziert".
  3. Dieses Modul beansprucht NICHT, "Layer 0" zu SEIN oder zu ersetzen.
     Der Name "Layer 0" ist im Repo bereits zweifach belegt
     (01_Framework/SKILL.md: "Immutable Foundation";
     docs/02_architecture/HEROIC_CORE_ORCHESTRATOR.md: "MasterSeed") —
     eine dritte Bedeutung wird bewusst NICHT eingefuehrt (siehe A13).
  4. Die Kanonisierung folgt bewusst derselben Konvention wie das bereits
     bewiesene fusion_hero_os.core.quantum_dictionaries.canonical_key()
     (json.dumps mit sort_keys=True, separators=(",", ":")), wird hier aber
     lokal implementiert statt importiert, damit dieses Modul ein wirklich
     eigenstaendiger, repo-unabhaengiger Baustein bleibt (kein Import ueber
     die ascension_os/fusion_hero_os-Grenze).
  5. Anders als MinerIdentity (crypto_identity.py) schreibt dieses Modul
     KEINE Schluesseldatei als Seiteneffekt — Schluessel leben nur im
     Prozessspeicher der jeweiligen Instanz.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


def canonical_bytes(manifest: Dict[str, Any]) -> bytes:
    """Deterministische Byte-Form eines Manifest-Dicts — die
    Schluessel-Reihenfolge im Quell-Dict beeinflusst das Ergebnis nicht."""
    canonical = json.dumps(
        manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        default=str,
    )
    return canonical.encode("utf-8")


@dataclass
class AnchorKeyPair:
    private_key: Ed25519PrivateKey
    public_key: Ed25519PublicKey

    def public_bytes_hex(self) -> str:
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ).hex()


def generate_keypair() -> AnchorKeyPair:
    private_key = Ed25519PrivateKey.generate()
    return AnchorKeyPair(private_key=private_key, public_key=private_key.public_key())


def sign_manifest(private_key: Ed25519PrivateKey, manifest: Dict[str, Any]) -> str:
    """Signiert die kanonische Byte-Form von manifest, liefert Hex-Signatur."""
    return private_key.sign(canonical_bytes(manifest)).hex()


def verify_manifest(public_key_hex: str, manifest: Dict[str, Any],
                    signature_hex: str) -> bool:
    """True NUR, wenn signature_hex exakt zu (public_key_hex, kanonischem
    manifest) passt. Liefert False statt einer Exception bei jeder Form von
    Manipulation ODER syntaktisch ungueltigem Hex-Input (fail-closed)."""
    try:
        public_key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(public_key_hex))
        public_key.verify(bytes.fromhex(signature_hex), canonical_bytes(manifest))
        return True
    except Exception:
        return False


class RootAnchorHandshake:
    """Prozess-lokales Sign+Verify ueber ein Manifest-Dict."""

    def __init__(self, keypair: Optional[AnchorKeyPair] = None):
        self.keypair = keypair or generate_keypair()

    def sign(self, manifest: Dict[str, Any]) -> str:
        return sign_manifest(self.keypair.private_key, manifest)

    def verify(self, manifest: Dict[str, Any], signature_hex: str,
               public_key_hex: Optional[str] = None) -> bool:
        pub_hex = public_key_hex or self.keypair.public_bytes_hex()
        return verify_manifest(pub_hex, manifest, signature_hex)


if __name__ == "__main__":
    anchor = RootAnchorHandshake()
    demo = {"layer": "ascension", "claim": "healthy", "checkpoint": 3}
    sig = anchor.sign(demo)
    print("public_key:", anchor.keypair.public_bytes_hex())
    print("signature :", sig[:32] + "...")
    print("verify    :", anchor.verify(demo, sig))
    print("tampered  :", anchor.verify(dict(demo, claim="compromised"), sig))
