"""
Dead-Letterbox Pseudo-Attack Simulation — lab only.

Operationalizes a *pseudo* adversary that only ever posts into local
"dead letterboxes" (in-memory / ~/.fusion queues that never deliver mail
or packets to third parties). Used to exercise defensive detectors on
the Fusion Hero OS stack under Meister Hasch sandbox rules.

What this IS:
  - Closed-loop simulation of noisy probes from synthetic / retired box IDs
  - Property tests: insecure mock defender vs secure mock defender
  - Evidence under ~/.fusion/alerts/ + docs/security/ summary

What this is NOT:
  - Real email (no SMTP/IMAP)
  - Scans or exploits against external hosts (Palantir or anyone)
  - Live "hyper mode" combat

Policy: sandbox_only · no_external_targets · freemium=false · Meister Hasch labor
Geltung: Spezifikation (sandbox outcomes) · MODELL (mapping to real ops)
"""
from __future__ import annotations

import hashlib
import json
import random
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ALERT_DIR = Path.home() / ".fusion" / "alerts"
DOCS_SUMMARY = ROOT / "docs" / "security" / "dead_letterbox_pseudo_attack.summary.json"

__all__ = [
    "DeadLetterbox",
    "PseudoProbe",
    "MockDefender",
    "run_pseudo_attack_sim",
    "status",
]

# Hard denylist fragments — if a probe target contains these, refuse to run
_FORBIDDEN_TARGET_MARKERS = (
    "palantir.com",
    "palantirtech",
    "foundry.palantir",
    "gotham.",
    # generic third-party live hosts (simulation must stay .lab / .local / in-memory)
)


@dataclass
class DeadLetterbox:
    """A mailbox that never delivers — only enqueues locally."""

    box_id: str
    label: str
    retired: bool = True
    messages: list[dict[str, Any]] = field(default_factory=list)

    def deposit(self, payload: dict[str, Any]) -> str:
        mid = hashlib.sha256(
            f"{self.box_id}:{time.time_ns()}:{payload}".encode()
        ).hexdigest()[:16]
        entry = {
            "message_id": mid,
            "deposited_at": datetime.now(UTC).isoformat(),
            "payload": payload,
            "delivered": False,  # always false — dead box
            "channel": "dead_letterbox_local",
        }
        self.messages.append(entry)
        return mid


@dataclass
class PseudoProbe:
    """Synthetic probe originating from a dead letterbox (not a real sender)."""

    probe_id: str
    from_box: str
    intent: str  # e.g. "fractal_marker_noise" | "integrity_ping" | "replay_noise"
    body: str
    target_surface: str  # must be lab-local

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DefenseVerdict:
    probe_id: str
    accepted: bool
    disposition: str  # "blocked" | "dead_lettered" | "accepted_insecure" | "rejected_forbidden"
    reason: str
    confidence: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MockDefender:
    """
    Local defender of *own* lab surfaces.

    secure=True: drops pseudo-attacks into dead letter + blocks
    secure=False: naively accepts (property-test only)
    """

    def __init__(self, *, secure: bool = True, sandbox_only: bool = True):
        if not sandbox_only:
            raise ValueError(
                "dead_letterbox_pseudo_attack_sim refuses sandbox_only=False"
            )
        self.secure = secure
        self.sandbox_only = sandbox_only
        self.inbox_lab: list[dict[str, Any]] = []
        self.dead_letters: list[dict[str, Any]] = []
        self.verdicts: list[DefenseVerdict] = []

    def _forbidden_target(self, surface: str) -> bool:
        s = surface.lower()
        if any(m in s for m in _FORBIDDEN_TARGET_MARKERS):
            return True
        # only allow lab-local naming conventions
        if not re.search(r"(\.lab\b|\.local\b|lab://|fusion\.local|ascension\.lab)", s):
            if not s.startswith("own:") and not s.startswith("mock:"):
                return True
        return False

    def receive(self, probe: PseudoProbe, box: DeadLetterbox) -> DefenseVerdict:
        if self._forbidden_target(probe.target_surface):
            v = DefenseVerdict(
                probe_id=probe.probe_id,
                accepted=False,
                disposition="rejected_forbidden",
                reason="target not lab-local or on denylist — no external targets",
                confidence=1.0,
            )
            self.verdicts.append(v)
            return v

        # Always deposit a copy into the dead letterbox (simulation telemetry)
        box.deposit(
            {
                "probe_id": probe.probe_id,
                "intent": probe.intent,
                "target": probe.target_surface,
                "body_sha16": hashlib.sha256(probe.body.encode()).hexdigest()[:16],
            }
        )

        if self.secure:
            # Operationalize: route to dead letter, never accept as live action
            self.dead_letters.append(probe.to_dict())
            v = DefenseVerdict(
                probe_id=probe.probe_id,
                accepted=False,
                disposition="dead_lettered",
                reason="secure defender: pseudo-attack quarantined in dead letter",
                confidence=0.92,
            )
        else:
            # Insecure mock — accepts noise (for property contrast only)
            self.inbox_lab.append(probe.to_dict())
            v = DefenseVerdict(
                probe_id=probe.probe_id,
                accepted=True,
                disposition="accepted_insecure",
                reason="insecure mock: accepted probe without quarantine",
                confidence=0.55,
            )
        self.verdicts.append(v)
        return v


def _synthetic_boxes(n: int = 3, seed: int = 42) -> list[DeadLetterbox]:
    rng = random.Random(seed)
    boxes = []
    for i in range(n):
        bid = f"deadbox-{rng.randint(1000, 9999):04d}-{i}"
        boxes.append(
            DeadLetterbox(
                box_id=bid,
                label=f"retired_synthetic_letterbox_{i}",
                retired=True,
            )
        )
    return boxes


def _synthetic_probes(boxes: list[DeadLetterbox], seed: int = 42) -> list[PseudoProbe]:
    rng = random.Random(seed + 7)
    intents = ("fractal_marker_noise", "integrity_ping", "replay_noise", "fluid_mask_jitter")
    probes = []
    for i, box in enumerate(boxes):
        for j in range(2):
            intent = intents[(i + j) % len(intents)]
            body = (
                f"PSEUDO:{intent}:from={box.box_id}:chunk="
                + ("A" * (40 + rng.randint(0, 30)))
            )
            probes.append(
                PseudoProbe(
                    probe_id=f"probe-{i}-{j}-{rng.randint(100, 999)}",
                    from_box=box.box_id,
                    intent=intent,
                    body=body,
                    target_surface="own:fusion.local/lab/integrity_sink",
                )
            )
    # One deliberately forbidden probe to prove the gate
    probes.append(
        PseudoProbe(
            probe_id="probe-forbidden-denylist",
            from_box=boxes[0].box_id,
            intent="external_probe_blocked",
            body="must_not_leave_lab",
            target_surface="https://www.palantir.com/",
        )
    )
    return probes


def run_pseudo_attack_sim(
    *,
    seed: int = 42,
    write_evidence: bool = True,
    sandbox_only: bool = True,
) -> dict[str, Any]:
    """
    Run dual-path sim: insecure mock vs secure mock, all from dead letterboxes.
    """
    if not sandbox_only:
        raise ValueError("sandbox_only=False forbidden")

    boxes = _synthetic_boxes(seed=seed)
    probes = _synthetic_probes(boxes, seed=seed)
    box_by_id = {b.box_id: b for b in boxes}

    insecure = MockDefender(secure=False, sandbox_only=True)
    secure = MockDefender(secure=True, sandbox_only=True)

    for p in probes:
        box = box_by_id.get(p.from_box) or boxes[0]
        insecure.receive(p, box)
        secure.receive(p, box)

    # Property expectations
    forbidden_insecure = [
        v for v in insecure.verdicts if v.disposition == "rejected_forbidden"
    ]
    forbidden_secure = [
        v for v in secure.verdicts if v.disposition == "rejected_forbidden"
    ]
    dead_lettered = [
        v for v in secure.verdicts if v.disposition == "dead_lettered"
    ]
    accepted_insecure = [
        v for v in insecure.verdicts if v.disposition == "accepted_insecure"
    ]

    properties = {
        "denylist_blocks_external_on_both": len(forbidden_insecure) >= 1
        and len(forbidden_secure) >= 1,
        "secure_quarantines_lab_probes": len(dead_lettered) >= 1,
        "insecure_accepts_lab_probes": len(accepted_insecure) >= 1,
        "no_message_marked_delivered": all(
            not m["delivered"] for b in boxes for m in b.messages
        ),
        "sandbox_only": True,
        "no_real_smtp": True,
        "no_external_targets": True,
    }
    all_pass = all(bool(v) for v in properties.values())

    report = {
        "kind": "dead_letterbox_pseudo_attack_sim",
        "generated_at": datetime.now(UTC).isoformat(),
        "platform_hint": "12.0.0",
        "policy": {
            "sandbox_only": True,
            "no_external_targets": True,
            "real_smtp": False,
            "meister_hasch_labor": True,
            "hyper_mode": "OFF",
            "offense": "FORBIDDEN",
            "pseudo_only": True,
        },
        "boxes": [
            {
                "box_id": b.box_id,
                "label": b.label,
                "retired": b.retired,
                "message_count": len(b.messages),
            }
            for b in boxes
        ],
        "probe_count": len(probes),
        "insecure": {
            "accepted": len(accepted_insecure),
            "forbidden": len(forbidden_insecure),
            "verdicts": [v.to_dict() for v in insecure.verdicts],
        },
        "secure": {
            "dead_lettered": len(dead_lettered),
            "forbidden": len(forbidden_secure),
            "verdicts": [v.to_dict() for v in secure.verdicts],
        },
        "properties": properties,
        "all_properties_pass": all_pass,
        "sha16": hashlib.sha256(
            json.dumps(properties, sort_keys=True).encode()
        ).hexdigest()[:16],
        "geltung": "Spezifikation (sandbox) · no real-world delivery",
        "doc": "docs/security/DEAD_LETTERBOX_PSEUDO_ATTACK_SIM.md",
    }

    if write_evidence:
        ALERT_DIR.mkdir(parents=True, exist_ok=True)
        alert_path = ALERT_DIR / "dead_letterbox_pseudo_attack_sim.json"
        alert_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        DOCS_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
        # Public-safe summary (no long verdict dumps)
        summary = {
            k: report[k]
            for k in (
                "kind",
                "generated_at",
                "policy",
                "probe_count",
                "properties",
                "all_properties_pass",
                "sha16",
                "geltung",
                "doc",
            )
        }
        summary["boxes"] = report["boxes"]
        summary["insecure_accepted"] = report["insecure"]["accepted"]
        summary["secure_dead_lettered"] = report["secure"]["dead_lettered"]
        summary["forbidden_blocked"] = report["secure"]["forbidden"]
        DOCS_SUMMARY.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        report["evidence_paths"] = {
            "alert": str(alert_path),
            "docs_summary": str(DOCS_SUMMARY),
        }

    return report


def status() -> dict[str, Any]:
    if DOCS_SUMMARY.is_file():
        return json.loads(DOCS_SUMMARY.read_text(encoding="utf-8"))
    return {"kind": "dead_letterbox_pseudo_attack_sim", "status": "never_run"}


def main(argv: list[str] | None = None) -> int:
    import argparse

    p = argparse.ArgumentParser(
        description="Dead-letterbox pseudo-attack sim (lab only, no real mail)"
    )
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--json", action="store_true")
    p.add_argument("--no-write", action="store_true")
    p.add_argument("--status", action="store_true")
    args = p.parse_args(argv)

    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0

    report = run_pseudo_attack_sim(
        seed=args.seed, write_evidence=not args.no_write, sandbox_only=True
    )
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            f"[dead_letterbox] probes={report['probe_count']} "
            f"secure_quarantined={report['secure']['dead_lettered']} "
            f"insecure_accepted={report['insecure']['accepted']} "
            f"forbidden_blocked={report['secure']['forbidden']} "
            f"all_pass={report['all_properties_pass']} sha16={report['sha16']}"
        )
        if "evidence_paths" in report:
            print(f"  alert: {report['evidence_paths']['alert']}")
            print(f"  summary: {report['evidence_paths']['docs_summary']}")
    return 0 if report["all_properties_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
