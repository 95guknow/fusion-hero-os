# -*- coding: utf-8 -*-
"""Tests fuer root_anchor_handshake: Ed25519 Sign/Verify, Tamper-Detection,
Kanonisierungs-Determinismus. Keine Netzwerk-/SSH-Tests — dieses Modul
implementiert keinen Transport. Proof-Registry-Anker: ROOT-ANCHOR-TAMPER-DETECT."""

from __future__ import annotations

from ascension_os.core.root_anchor_handshake import (
    RootAnchorHandshake,
    canonical_bytes,
    generate_keypair,
    sign_manifest,
    verify_manifest,
)

MANIFEST = {"layer": "ascension", "claim": "healthy", "checkpoint": 3}


def test_sign_then_verify_roundtrip_succeeds():
    kp = generate_keypair()
    sig = sign_manifest(kp.private_key, MANIFEST)
    assert verify_manifest(kp.public_bytes_hex(), MANIFEST, sig) is True


def test_tampered_manifest_fails_verification():
    kp = generate_keypair()
    sig = sign_manifest(kp.private_key, MANIFEST)
    tampered = dict(MANIFEST, claim="compromised")
    assert verify_manifest(kp.public_bytes_hex(), tampered, sig) is False


def test_tampered_signature_fails_verification():
    kp = generate_keypair()
    sig = sign_manifest(kp.private_key, MANIFEST)
    flipped = ("0" if sig[0] != "0" else "1") + sig[1:]
    assert verify_manifest(kp.public_bytes_hex(), MANIFEST, flipped) is False


def test_wrong_public_key_fails_verification():
    kp1 = generate_keypair()
    kp2 = generate_keypair()
    sig = sign_manifest(kp1.private_key, MANIFEST)
    assert verify_manifest(kp2.public_bytes_hex(), MANIFEST, sig) is False


def test_canonicalization_is_order_independent():
    m1 = {"a": 1, "b": 2, "c": 3}
    m2 = {"c": 3, "a": 1, "b": 2}
    assert canonical_bytes(m1) == canonical_bytes(m2)
    kp = generate_keypair()
    sig = sign_manifest(kp.private_key, m1)
    assert verify_manifest(kp.public_bytes_hex(), m2, sig) is True


def test_canonical_bytes_is_deterministic_across_calls():
    assert canonical_bytes(MANIFEST) == canonical_bytes(MANIFEST)


def test_invalid_hex_inputs_return_false_not_raise():
    assert verify_manifest("not-hex", MANIFEST, "also-not-hex") is False


def test_generate_keypair_produces_distinct_keys():
    kp1 = generate_keypair()
    kp2 = generate_keypair()
    assert kp1.public_bytes_hex() != kp2.public_bytes_hex()


def test_root_anchor_handshake_class_roundtrip():
    anchor = RootAnchorHandshake()
    sig = anchor.sign(MANIFEST)
    assert anchor.verify(MANIFEST, sig) is True


def test_root_anchor_handshake_class_rejects_foreign_signature():
    anchor_a = RootAnchorHandshake()
    anchor_b = RootAnchorHandshake()
    sig = anchor_a.sign(MANIFEST)
    assert anchor_b.verify(
        MANIFEST, sig, public_key_hex=anchor_b.keypair.public_bytes_hex()
    ) is False
