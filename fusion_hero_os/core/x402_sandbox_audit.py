"""
x402 Sandbox Security Audit — local, defensive, authorized lab only.

Purpose:
  Prove (in a closed sandbox) that missing protocol controls enable
  unpaid-service or paid-but-denied *classes* of failure — by unit-testing
  a mock resource server under SECURE vs INSECURE configurations.

Out of scope (never implemented here):
  - Real facilitator/mainnet attacks
  - Exploit payloads against third parties
  - Network propagation of attack tools

Evidence is written under ~/.fusion/alerts/ and docs/security/.

Geltung: Spezifikation (sandbox) · MODELL (mapping to public x402 research)
Policy: sandbox_only · no_external_targets · freemium=false
"""
from __future__ import annotations

import hashlib
import json
import secrets
import time
from dataclasses import asdict, dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

__all__ = [
    "SandboxConfig",
    "MockX402Server",
    "MockClient",
    "run_sandbox_audit",
    "status",
]


@dataclass
class SandboxConfig:
    """Toggle individual controls (secure = all True)."""

    nonce_single_use: bool = True
    finality_before_grant: bool = True
    bind_amount_resource: bool = True
    reject_unverified: bool = True
    no_cache_paid: bool = True
    agent_allowlist: bool = True
    # Simulated settlement: if False, grant happens before "finality"
    settlement_finalized: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PaymentAuth:
    payment_id: str
    nonce: str
    amount: str
    resource: str
    payee: str
    verified: bool = False
    settled: bool = False


@dataclass
class EvidenceCase:
    id: str
    title: str
    control: str
    insecure_outcome: str
    secure_outcome: str
    proved: bool
    detail: str
    severity: str = "high"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MockX402Server:
    """In-memory x402-like resource server for defensive property tests."""

    def __init__(self, cfg: SandboxConfig, *, allowlist: set[str] | None = None):
        self.cfg = cfg
        self.allowlist = allowlist or {"https://api.example.local/v1/data"}
        self._used_nonces: set[str] = set()
        self._used_payment_ids: set[str] = set()
        self._grants: list[dict[str, Any]] = []
        self.payee_canonical = "0xPAYEE_CANONICAL"
        self.price = "0.01"
        self.resource_path = "https://api.example.local/v1/data"

    def challenge(self, resource: str) -> dict[str, Any]:
        """HTTP 402 analogue."""
        return {
            "status": 402,
            "PAYMENT-REQUIRED": {
                "amount": self.price,
                "payee": self.payee_canonical,
                "resource": resource,
                "paymentId": secrets.token_hex(8),
                "nonce": secrets.token_hex(8),
                "expiresAt": time.time() + 120,
            },
        }

    def _bind_ok(self, auth: PaymentAuth) -> bool:
        if not self.cfg.bind_amount_resource:
            return True  # insecure: accept any binding
        return (
            auth.amount == self.price
            and auth.resource == self.resource_path
            and auth.payee == self.payee_canonical
        )

    def grant(self, auth: PaymentAuth, *, client_host: str = "agent.local") -> dict[str, Any]:
        """Attempt to grant resource after payment auth (sandbox)."""
        # Allowlist
        if self.cfg.agent_allowlist and auth.resource not in self.allowlist:
            return {"status": 403, "error": "resource_not_allowlisted", "granted": False}

        # Verified by facilitator mock
        if self.cfg.reject_unverified and not auth.verified:
            return {"status": 402, "error": "unverified_payment", "granted": False}

        # Finality
        if self.cfg.finality_before_grant and not (
            auth.settled and self.cfg.settlement_finalized
        ):
            return {"status": 402, "error": "settlement_not_final", "granted": False}

        # Binding
        if not self._bind_ok(auth):
            return {"status": 402, "error": "binding_mismatch", "granted": False}

        # Replay / single-use
        if self.cfg.nonce_single_use:
            if auth.nonce in self._used_nonces or auth.payment_id in self._used_payment_ids:
                return {"status": 402, "error": "replay_rejected", "granted": False}
            self._used_nonces.add(auth.nonce)
            self._used_payment_ids.add(auth.payment_id)
        else:
            # insecure: still record but do not reject duplicates
            self._used_nonces.add(auth.nonce)
            self._used_payment_ids.add(auth.payment_id)

        grant = {
            "status": 200,
            "granted": True,
            "resource": auth.resource,
            "payment_id": auth.payment_id,
            "cache_control": "private, no-store" if self.cfg.no_cache_paid else "public, max-age=3600",
        }
        self._grants.append(grant)
        return grant


class MockClient:
    def __init__(self, server: MockX402Server):
        self.server = server

    def pay_and_request(
        self,
        *,
        amount: str | None = None,
        resource: str | None = None,
        payee: str | None = None,
        verified: bool = True,
        settled: bool = True,
        reuse_auth: PaymentAuth | None = None,
    ) -> tuple[PaymentAuth, dict[str, Any]]:
        if reuse_auth is not None:
            return reuse_auth, self.server.grant(reuse_auth)

        ch = self.server.challenge(resource or self.server.resource_path)
        pr = ch["PAYMENT-REQUIRED"]
        auth = PaymentAuth(
            payment_id=pr["paymentId"],
            nonce=pr["nonce"],
            amount=amount if amount is not None else pr["amount"],
            resource=resource if resource is not None else pr["resource"],
            payee=payee if payee is not None else pr["payee"],
            verified=verified,
            settled=settled,
        )
        return auth, self.server.grant(auth)


def _case_replay() -> EvidenceCase:
    """Prove: without nonce single-use, same payment grants twice."""
    insecure = MockX402Server(SandboxConfig(nonce_single_use=False))
    client = MockClient(insecure)
    auth, g1 = client.pay_and_request()
    _, g2 = client.pay_and_request(reuse_auth=auth)
    insecure_ok = g1.get("granted") and g2.get("granted")

    secure = MockX402Server(SandboxConfig(nonce_single_use=True))
    client2 = MockClient(secure)
    auth2, s1 = client2.pay_and_request()
    _, s2 = client2.pay_and_request(reuse_auth=auth2)
    secure_ok = s1.get("granted") and (not s2.get("granted")) and s2.get("error") == "replay_rejected"

    return EvidenceCase(
        id="E_REPLAY",
        title="Replay / missing single-use payment proof",
        control="G_nonce_single_use",
        insecure_outcome="one_payment_many_grants" if insecure_ok else "unexpected",
        secure_outcome="second_grant_rejected" if secure_ok else "unexpected",
        proved=bool(insecure_ok and secure_ok),
        detail=f"insecure grants={len(insecure._grants)} secure_second={s2}",
        severity="critical",
    )


def _case_finality() -> EvidenceCase:
    """Prove: without finality gate, unsettled auth still grants."""
    insecure = MockX402Server(
        SandboxConfig(finality_before_grant=False, settlement_finalized=False)
    )
    _, g = MockClient(insecure).pay_and_request(settled=False)
    insecure_ok = g.get("granted") is True

    secure = MockX402Server(
        SandboxConfig(finality_before_grant=True, settlement_finalized=True)
    )
    # settled=False must not grant
    _, s = MockClient(secure).pay_and_request(settled=False)
    secure_ok = s.get("granted") is False and s.get("error") == "settlement_not_final"
    # settled=True grants
    _, s2 = MockClient(secure).pay_and_request(settled=True)
    secure_ok = secure_ok and s2.get("granted") is True

    return EvidenceCase(
        id="E_FINALITY",
        title="Optimistic grant before settlement finality",
        control="G_finality_before_grant",
        insecure_outcome="grant_without_settlement" if insecure_ok else "unexpected",
        secure_outcome="reject_until_final" if secure_ok else "unexpected",
        proved=bool(insecure_ok and secure_ok),
        detail=f"insecure={g} secure_unsettled={s}",
        severity="high",
    )


def _case_binding() -> EvidenceCase:
    """Prove: without binding, payee/resource swap still grants."""
    insecure = MockX402Server(SandboxConfig(bind_amount_resource=False))
    _, g = MockClient(insecure).pay_and_request(
        payee="0xATTACKER", resource="https://evil.local/steal"
    )
    # also need allowlist off for evil resource
    insecure2 = MockX402Server(
        SandboxConfig(bind_amount_resource=False, agent_allowlist=False)
    )
    _, g = MockClient(insecure2).pay_and_request(
        payee="0xATTACKER", resource="https://evil.local/steal"
    )
    insecure_ok = g.get("granted") is True

    secure = MockX402Server(SandboxConfig(bind_amount_resource=True, agent_allowlist=True))
    _, s = MockClient(secure).pay_and_request(payee="0xATTACKER")
    secure_ok = s.get("granted") is False and s.get("error") == "binding_mismatch"

    return EvidenceCase(
        id="E_BINDING",
        title="Amount/resource/payee binding mismatch",
        control="G_bind_amount_resource",
        insecure_outcome="grant_with_swapped_payee" if insecure_ok else "unexpected",
        secure_outcome="binding_reject" if secure_ok else "unexpected",
        proved=bool(insecure_ok and secure_ok),
        detail=f"insecure={g} secure={s}",
        severity="critical",
    )


def _case_unverified() -> EvidenceCase:
    insecure = MockX402Server(SandboxConfig(reject_unverified=False))
    _, g = MockClient(insecure).pay_and_request(verified=False)
    insecure_ok = g.get("granted") is True

    secure = MockX402Server(SandboxConfig(reject_unverified=True))
    _, s = MockClient(secure).pay_and_request(verified=False)
    secure_ok = s.get("granted") is False and s.get("error") == "unverified_payment"

    return EvidenceCase(
        id="E_UNVERIFIED",
        title="Unverified payment header accepted",
        control="G_reject_unverified_header",
        insecure_outcome="grant_unverified" if insecure_ok else "unexpected",
        secure_outcome="reject_unverified" if secure_ok else "unexpected",
        proved=bool(insecure_ok and secure_ok),
        detail=f"insecure={g} secure={s}",
        severity="high",
    )


def _case_cache_header() -> EvidenceCase:
    """Prove cache policy differs (defensive header property)."""
    insecure = MockX402Server(SandboxConfig(no_cache_paid=False))
    _, g = MockClient(insecure).pay_and_request()
    insecure_ok = g.get("granted") and "public" in str(g.get("cache_control", ""))

    secure = MockX402Server(SandboxConfig(no_cache_paid=True))
    _, s = MockClient(secure).pay_and_request()
    secure_ok = s.get("granted") and "no-store" in str(s.get("cache_control", ""))

    return EvidenceCase(
        id="E_CACHE",
        title="Paid response cacheability (header/proxy class)",
        control="G_no_cache_paid_body",
        insecure_outcome="public_cacheable" if insecure_ok else "unexpected",
        secure_outcome="no_store" if secure_ok else "unexpected",
        proved=bool(insecure_ok and secure_ok),
        detail=f"insecure_cc={g.get('cache_control')} secure_cc={s.get('cache_control')}",
        severity="high",
    )


def _case_allowlist() -> EvidenceCase:
    # Isolate allowlist: disable binding so only allowlist decides
    insecure = MockX402Server(
        SandboxConfig(agent_allowlist=False, bind_amount_resource=False)
    )
    _, g = MockClient(insecure).pay_and_request(resource="https://sybil.evil/payme")
    insecure_ok = g.get("granted") is True

    secure = MockX402Server(
        SandboxConfig(agent_allowlist=True, bind_amount_resource=False)
    )
    _, s = MockClient(secure).pay_and_request(resource="https://sybil.evil/payme")
    secure_ok = s.get("granted") is False and s.get("error") == "resource_not_allowlisted"

    return EvidenceCase(
        id="E_ALLOWLIST",
        title="Agent server-selection / non-allowlisted resource",
        control="G_agent_allowlist",
        insecure_outcome="grant_any_url" if insecure_ok else "unexpected",
        secure_outcome="reject_unknown_host" if secure_ok else "unexpected",
        proved=bool(insecure_ok and secure_ok),
        detail=f"insecure={g} secure={s}",
        severity="medium",
    )


def simulate_successful_attack(
    *,
    public_damage_eur_cents: float = 0.01,
    dormant_days: int = 900,
) -> dict[str, Any]:
    """
    Aussagekräftige Angriffssimulation (nur insecure Mock).

    Öffentlicher Schadensrahmen: 0,01 ct (= 0,0001 EUR) — modelliert als
    Micropayment-Wert einer *langzeit-inaktiven* Lab-Wallet (keine echten Funds).

    Narrative (lab):
      0) Dormant wallet profile (long inactivity)
      1) 402 challenge at 0,01 ct economic unit
      2) Forged auth: redirect value to attacker payee; no verify/finality
      3) GRANT_1 succeeds (unbound / unpaid class)
      4) REPLAY → GRANT_2 (double spend of grant right)
      5) Secure mock blocks same chain

    No on-chain transfer. Damage figure is the *authorized public damage envelope*.
    """
    # "0,01 ct" = 0.01 Eurocent = 0.0001 EUR (public damage envelope)
    amount_ct = float(public_damage_eur_cents)  # parameter name: amount in ct units
    damage_eur = amount_ct / 100.0
    damage_label = f"{amount_ct:g} ct (Eurocent)"
    price_str = f"{damage_eur:.10f}".rstrip("0").rstrip(".")

    dormant_wallet = {
        "label": "LANGZEIT_INAKTIVE_LAB_WALLET",
        "address_mock": "0xD0RMA17_INACTIVE_LAB_WALLET_NOT_REAL",
        "last_activity_days_ago": int(dormant_days),
        "last_activity_iso": (
            datetime.now(UTC).timestamp() - dormant_days * 86400
        ),
        "balance_eur_equivalent_mock": damage_eur,
        "note": "Mock identity only — no private key, no chain broadcast",
    }
    dormant_wallet["last_activity_iso"] = datetime.fromtimestamp(
        float(dormant_wallet["last_activity_iso"]), tz=UTC
    ).isoformat()

    # --- INSECURE: all critical controls off ---
    insecure_cfg = SandboxConfig(
        nonce_single_use=False,
        finality_before_grant=False,
        bind_amount_resource=False,
        reject_unverified=False,
        no_cache_paid=False,
        agent_allowlist=False,
        settlement_finalized=False,
    )
    victim = MockX402Server(insecure_cfg)
    victim.price = price_str
    victim.payee_canonical = dormant_wallet["address_mock"]  # value notionally from dormant wallet

    timeline: list[dict[str, Any]] = []
    timeline.append(
        {
            "step": 0,
            "action": "SELECT_DORMANT_WALLET",
            "wallet": dormant_wallet,
            "public_damage": {
                "amount": damage_label,
                "eur": damage_eur,
                "justification": "Minimal public damage envelope for meaningful lab proof",
            },
        }
    )

    ch = victim.challenge(victim.resource_path)
    # Stamp economic unit into challenge
    ch["PAYMENT-REQUIRED"]["amount"] = price_str
    ch["PAYMENT-REQUIRED"]["amount_label"] = damage_label
    ch["PAYMENT-REQUIRED"]["payee"] = dormant_wallet["address_mock"]
    timeline.append({"step": 1, "action": "GET_resource", "result": "402_challenge", "body": ch})

    pr = ch["PAYMENT-REQUIRED"]
    forged = PaymentAuth(
        payment_id=pr["paymentId"],
        nonce=pr["nonce"],
        amount=price_str,
        resource=pr["resource"],
        payee="0xATTACKER_WALLET_SANDBOX_ONLY",
        verified=False,
        settled=False,
    )
    timeline.append(
        {
            "step": 2,
            "action": "FORGE_AND_REDIRECT_VALUE",
            "from_dormant_payee": dormant_wallet["address_mock"],
            "to_attacker_payee": forged.payee,
            "amount_label": damage_label,
            "eur": damage_eur,
            "verified": False,
            "settled": False,
            "classes": [
                "A8_amount_binding",
                "A3_replay_idempotency",
                "A1_settlement_optimistic",
                "A2_settlement_preempt",
            ],
        }
    )

    g1 = victim.grant(forged)
    timeline.append({"step": 3, "action": "GRANT_1_SUCCESS", "result": g1})
    g2 = victim.grant(forged)
    timeline.append({"step": 4, "action": "REPLAY_GRANT_2_SUCCESS", "result": g2})

    attack_success = bool(g1.get("granted") and g2.get("granted"))
    # Economic impact: 2 grants × 0,01 ct value unit (grant-right double spend)
    economic = {
        "unit_label": damage_label,
        "unit_eur": damage_eur,
        "grants": len(victim._grants),
        "notional_value_eur": round(damage_eur * max(1, len(victim._grants)), 10),
        "notional_value_label": f"{amount_ct * max(1, len(victim._grants)):g} ct (notional)",
        "source_wallet": "langzeit_inaktiv_lab",
        "real_chain_transfer": False,
        "public_damage_cap_statement": (
            "Öffentlicher Schadensrahmen dieser Simulation: 0,01 ct "
            "bezogen auf eine langzeit-inaktive Lab-Wallet (Mock). "
            "Keine On-Chain-Bewegung."
        ),
    }
    impact = {
        "unpaid_or_unbound_grants": len(victim._grants),
        "payee_attacker": forged.payee,
        "payee_victim_dormant": dormant_wallet["address_mock"],
        "cache_control": g1.get("cache_control"),
        "replay_worked": g2.get("granted") is True,
        "economic": economic,
        "dormant_wallet": dormant_wallet,
    }

    # --- SECURE: same sequence must fail ---
    secure = MockX402Server(SandboxConfig())
    secure.price = price_str
    secure.payee_canonical = dormant_wallet["address_mock"]
    g_secure = secure.grant(forged)
    secure_blocked = g_secure.get("granted") is False

    sim = {
        "ok": attack_success and secure_blocked,
        "simulation": True,
        "sandbox_only": True,
        "external_targets": False,
        "exploit_payloads": False,
        "real_chain_transfer": False,
        "attack_name": "SANDBOX_DORMANT_WALLET_0_01CT_REPLAY_REDIRECT",
        "public_damage": {
            "amount_ct": 0.01,
            "amount_eur": damage_eur,
            "label": damage_label,
            "wallet_class": "langzeit_inaktiv",
            "dormant_days": dormant_days,
        },
        "attack_succeeded_on_insecure_mock": attack_success,
        "attack_blocked_on_secure_mock": secure_blocked,
        "impact": impact,
        "timeline": timeline,
        "secure_block_result": g_secure,
        "generated_at": datetime.now(UTC).isoformat(),
        "meaningfulness": (
            "Aussagekräftig durch (1) realistische Micropayment-Größe 0,01 ct, "
            "(2) langzeit-inaktive Wallet als Wertquelle, (3) durchgängigen "
            "Angriffspfad inkl. Replay, (4) Kontrast Secure-Block."
        ),
        "disclaimer": (
            "Local insecure mock only. Notional 0,01 ct public-damage envelope "
            "from a long-inactive lab wallet identity. No private keys, no broadcast, "
            "no live x402/facilitator attack."
        ),
        "geltung": "Spezifikation (sandbox simulation) · Schadenszahl = deklarierter Lab-Rahmen",
    }
    sim["sha16"] = hashlib.sha256(
        json.dumps(sim, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]

    alert_dir = Path.home() / ".fusion" / "alerts"
    alert_dir.mkdir(parents=True, exist_ok=True)
    jpath = alert_dir / "x402_sandbox_attack_sim.json"
    jpath.write_text(json.dumps(sim, indent=2, ensure_ascii=False), encoding="utf-8")

    md = alert_dir / "X402_SANDBOX_ATTACK_SIMULATION.md"
    md.write_text(
        "\n".join(
            [
                "# x402 Sandbox — Aussagekräftige Angriffssimulation",
                "",
                f"**Time:** {sim['generated_at']}",
                f"**Attack succeeded (insecure):** {attack_success}",
                f"**Blocked (secure):** {secure_blocked}",
                f"**SHA16:** `{sim['sha16']}`",
                "",
                "## Öffentlicher Schaden (Lab-Rahmen)",
                "",
                f"- **Betrag:** **0,01 ct** (= {damage_eur} EUR)",
                f"- **Quelle:** langzeit-inaktive Lab-Wallet (`{dormant_days}` Tage ohne Aktivität)",
                f"- **Adresse (Mock):** `{dormant_wallet['address_mock']}`",
                "- **On-Chain:** **nein** (keine private keys, kein Broadcast)",
                f"- **Notional bei 2 Grants:** {economic['notional_value_label']}",
                "",
                "## Timeline",
                "",
                "0. Auswahl langzeit-inaktiver Wallet (Mock-Balance = 0,01 ct)",
                "1. Resource → 402 Challenge (amount = 0,01 ct)",
                "2. Forge auth: Payee → Attacker, verified=false, settled=false",
                "3. **GRANT_1 SUCCESS** (insecure)",
                "4. **REPLAY GRANT_2 SUCCESS** (insecure)",
                "5. Secure mock: **BLOCK**",
                "",
                "## Warum aussagekräftig",
                "",
                sim["meaningfulness"],
                "",
                "## Policy",
                "",
                "- Sandbox only · Schaden öffentlich deklariert 0,01 ct · kein realer Entzug",
                "- Dient der Notfall-Warnung und Gate-Notwendigkeit",
                "",
                f"JSON: `{jpath}`",
                "",
            ]
        ),
        encoding="utf-8",
    )

    docs = ROOT / "docs" / "security"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "x402_attack_sim.summary.json").write_text(
        json.dumps(
            {
                "generated_at": sim["generated_at"],
                "attack_succeeded_on_insecure_mock": attack_success,
                "attack_blocked_on_secure_mock": secure_blocked,
                "public_damage_ct": 0.01,
                "public_damage_eur": damage_eur,
                "dormant_days": dormant_days,
                "grants": impact["unpaid_or_unbound_grants"],
                "real_chain_transfer": False,
                "sha16": sim["sha16"],
                "sandbox_only": True,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    sim["evidence_paths"] = [str(jpath), str(md), str(docs / "x402_attack_sim.summary.json")]
    return sim


def run_sandbox_audit(*, budget_eur: float = 500.0) -> dict[str, Any]:
    """Run full local sandbox evidence suite + write proof artifacts."""
    # Import math audit for combined evidence
    from fusion_hero_os.core.x402_hackability_audit import audit as threat_audit

    cases = [
        _case_replay(),
        _case_finality(),
        _case_binding(),
        _case_unverified(),
        _case_cache_header(),
        _case_allowlist(),
    ]
    proved = sum(1 for c in cases if c.proved)
    threat = threat_audit(emit=True)

    report = {
        "ok": proved == len(cases),
        "sandbox": True,
        "external_targets": False,
        "exploit_payloads": False,
        "scope": {
            "type": "authorized_local_security_audit_sandbox",
            "budget_eur_cap": budget_eur,
            "budget_used_eur": 0.0,  # compute-only lab; no paid chain probes
            "budget_note": "Lab is local CPU only; €500 reserved for external human review if needed",
            "network": "none",
            "github_propagation": "docs_and_evidence_only_no_attack_tools",
        },
        "protocol": "x402",
        "generated_at": datetime.now(UTC).isoformat(),
        "evidence_cases": [c.to_dict() for c in cases],
        "proved_count": proved,
        "case_count": len(cases),
        "threat_audit": {
            "level": threat.level,
            "risk_score": threat.risk_score,
            "warn": threat.warn,
            "controls": f"{threat.controls_ok}/{threat.controls_total}",
        },
        "heroic_math": [m.to_dict() for m in threat.math_checks],
        "conclusion": (
            "Sandbox proves control necessity: insecure configs enable grant-abuse classes "
            "(replay, pre-finality, binding swap, unverified header, cache, sybil URL). "
            "Secure configs reject them. Not a claim about any live facilitator deployment."
        ),
        "geltung": "Spezifikation (sandbox properties) · MODELL (x402 public threat mapping)",
    }
    report["sha16"] = hashlib.sha256(
        json.dumps(report, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]

    # Persist evidence
    alert_dir = Path.home() / ".fusion" / "alerts"
    alert_dir.mkdir(parents=True, exist_ok=True)
    ev_path = alert_dir / "x402_sandbox_evidence.json"
    ev_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    md_path = alert_dir / "X402_SANDBOX_AUDIT_PROOF.md"
    lines = [
        "# x402 Sandbox Security Audit — Proof",
        "",
        f"**Time:** {report['generated_at']}",
        f"**Budget cap:** €{budget_eur:.0f} (lab used €0 chain fees)",
        f"**Proved cases:** {proved}/{len(cases)}",
        "**External targets:** none · **Exploit payloads:** none",
        f"**Threat score (gates open):** {threat.risk_score} ({threat.level})",
        "",
        "## Evidence cases (secure vs insecure mock)",
        "",
    ]
    for c in cases:
        mark = "PROVED" if c.proved else "FAIL"
        lines.append(f"### [{mark}] {c.id} — {c.title}")
        lines.append(f"- Control: `{c.control}` · Severity: {c.severity}")
        lines.append(f"- Insecure: `{c.insecure_outcome}`")
        lines.append(f"- Secure: `{c.secure_outcome}`")
        lines.append(f"- Detail: `{c.detail}`")
        lines.append("")
    lines.extend(
        [
            "## Conclusion",
            "",
            report["conclusion"],
            "",
            f"JSON: `{ev_path}`",
            f"SHA16: `{report['sha16']}`",
            "",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    docs = ROOT / "docs" / "security"
    docs.mkdir(parents=True, exist_ok=True)
    pub = {
        "generated_at": report["generated_at"],
        "proved_count": proved,
        "case_count": len(cases),
        "sandbox": True,
        "external_targets": False,
        "budget_eur_cap": budget_eur,
        "threat_level": threat.level,
        "threat_score": threat.risk_score,
        "case_ids": [c.id for c in cases if c.proved],
        "sha16": report["sha16"],
    }
    (docs / "x402_sandbox_proof.summary.json").write_text(
        json.dumps(pub, indent=2), encoding="utf-8"
    )
    (docs / "X402_SANDBOX_AUDIT.md").write_text(
        "\n".join(
            [
                "# x402 Sandbox Security Audit",
                "",
                "Local authorized lab. No external systems attacked. No exploit payloads.",
                "",
                "See operator proof: `~/.fusion/alerts/X402_SANDBOX_AUDIT_PROOF.md`",
                "Summary: `docs/security/x402_sandbox_proof.summary.json`",
                "",
                "```powershell",
                "python -m fusion_hero_os.core.x402_sandbox_audit",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )

    report["evidence_paths"] = [
        str(ev_path),
        str(md_path),
        str(docs / "x402_sandbox_proof.summary.json"),
        str(docs / "X402_SANDBOX_AUDIT.md"),
    ]
    return report


def status() -> dict[str, Any]:
    p = Path.home() / ".fusion" / "alerts" / "x402_sandbox_evidence.json"
    last = None
    if p.is_file():
        try:
            last = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            last = {"raw": True}
    return {
        "ok": True,
        "sandbox": True,
        "last_evidence": {
            "proved_count": (last or {}).get("proved_count"),
            "sha16": (last or {}).get("sha16"),
            "generated_at": (last or {}).get("generated_at"),
        }
        if last
        else None,
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="x402 local sandbox security audit (defensive)")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--budget-eur", type=float, default=500.0)
    ap.add_argument(
        "--simulate-attack",
        action="store_true",
        help="Run successful attack path against INSECURE mock only (sandbox)",
    )
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    if args.simulate_attack:
        sim = simulate_successful_attack()
        print(
            json.dumps(
                {
                    "ok": sim["ok"],
                    "simulation": True,
                    "sandbox_only": True,
                    "attack_succeeded_on_insecure_mock": sim[
                        "attack_succeeded_on_insecure_mock"
                    ],
                    "attack_blocked_on_secure_mock": sim["attack_blocked_on_secure_mock"],
                    "impact": sim["impact"],
                    "timeline_steps": len(sim["timeline"]),
                    "sha16": sim["sha16"],
                    "evidence_paths": sim["evidence_paths"],
                    "disclaimer": sim["disclaimer"],
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0 if sim["ok"] else 1
    report = run_sandbox_audit(budget_eur=args.budget_eur)
    print(
        json.dumps(
            {
                "ok": report["ok"],
                "proved": f"{report['proved_count']}/{report['case_count']}",
                "sandbox": True,
                "external_targets": False,
                "budget_eur_cap": report["scope"]["budget_eur_cap"],
                "budget_used_eur": report["scope"]["budget_used_eur"],
                "threat": report["threat_audit"],
                "cases": [
                    {"id": c["id"], "proved": c["proved"], "severity": c["severity"]}
                    for c in report["evidence_cases"]
                ],
                "sha16": report["sha16"],
                "evidence_paths": report["evidence_paths"],
                "conclusion": report["conclusion"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
