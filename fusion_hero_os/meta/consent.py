"""Consent, purpose, retention and append-only audit for the meta-neural slice.

Design goals (GDPR-oriented):

* **Explicit, revocable consent** — every privileged operation (ingest,
  association update, optimisation, persistence) requires a live
  :class:`ConsentGrant` naming a :class:`Purpose`.
* **Purpose limitation** — a grant authorises exactly one purpose. Using data
  for a different purpose is denied (fail closed).
* **Retention / expiry** — grants carry a retention window; expired or revoked
  grants authorise nothing.
* **Auditability** — every decision and every privileged operation produces an
  append-only :class:`AuditEvent`. The log cannot be mutated in place.

No covert profiling, surveillance, keylogging, target scoring or unconsented
human inference is implemented or permitted. Authorisation checks are the only
gate; there is deliberately no "bypass" path.
"""

from __future__ import annotations

import hashlib
import json
import threading
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from enum import Enum


def _utcnow() -> datetime:
    return datetime.now(UTC)


class Purpose(str, Enum):
    """Closed set of permitted, transparent purposes.

    The set is intentionally small and benign. There is no "surveillance",
    "profiling" or "scoring" purpose — such purposes are out of scope by policy.
    """

    INGEST = "ingest"
    WORKING_MEMORY = "working_memory"
    ASSOCIATION = "association"
    OPTIMIZATION = "optimization"
    PERSISTENCE = "persistence"
    AUDIT_READ = "audit_read"


class ConsentError(RuntimeError):
    """Raised when an operation is attempted without valid consent."""


@dataclass(frozen=True)
class ConsentGrant:
    """An explicit, revocable grant for a single subject and purpose."""

    grant_id: str
    subject_id: str
    purpose: Purpose
    granted_at: datetime
    retention: timedelta
    revoked_at: datetime | None = None

    def is_active(self, at: datetime | None = None) -> bool:
        at = at or _utcnow()
        if self.revoked_at is not None and at >= self.revoked_at:
            return False
        return at < self.expires_at

    @property
    def expires_at(self) -> datetime:
        return self.granted_at + self.retention

    def to_public_dict(self) -> dict[str, object]:
        """Serialise without any personal data (subject_id is an opaque id)."""
        return {
            "grant_id": self.grant_id,
            "subject_id": self.subject_id,
            "purpose": self.purpose.value,
            "granted_at": self.granted_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "revoked_at": self.revoked_at.isoformat() if self.revoked_at else None,
            "active": self.is_active(),
        }


@dataclass(frozen=True)
class AuditEvent:
    """A single append-only audit record.

    ``prev_hash``/``event_hash`` form a tamper-evident hash chain: each event
    commits to the previous one, so silent deletion or reordering is
    detectable via :meth:`AuditLog.verify`.
    """

    seq: int
    event_id: str
    timestamp: datetime
    action: str
    subject_id: str | None
    purpose: str | None
    decision: str  # "granted" | "denied" | "n/a"
    detail: dict[str, object]
    prev_hash: str
    event_hash: str

    def to_dict(self) -> dict[str, object]:
        return {
            "seq": self.seq,
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "action": self.action,
            "subject_id": self.subject_id,
            "purpose": self.purpose,
            "decision": self.decision,
            "detail": self.detail,
            "prev_hash": self.prev_hash,
            "event_hash": self.event_hash,
        }


def _hash_event(seq: int, timestamp: str, action: str, subject_id: str | None,
                purpose: str | None, decision: str, detail: dict[str, object],
                prev_hash: str) -> str:
    payload = json.dumps(
        {
            "seq": seq,
            "timestamp": timestamp,
            "action": action,
            "subject_id": subject_id,
            "purpose": purpose,
            "decision": decision,
            "detail": detail,
            "prev_hash": prev_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class AuditLog:
    """Append-only, tamper-evident audit log (in-memory, thread-safe)."""

    GENESIS_HASH = "0" * 64

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []
        self._lock = threading.RLock()

    def append(
        self,
        action: str,
        *,
        decision: str = "n/a",
        subject_id: str | None = None,
        purpose: str | None = None,
        detail: dict[str, object] | None = None,
        at: datetime | None = None,
    ) -> AuditEvent:
        with self._lock:
            seq = len(self._events)
            prev_hash = self._events[-1].event_hash if self._events else self.GENESIS_HASH
            ts = (at or _utcnow())
            ts_iso = ts.isoformat()
            safe_detail = dict(detail or {})
            event_hash = _hash_event(
                seq, ts_iso, action, subject_id, purpose, decision, safe_detail, prev_hash
            )
            event = AuditEvent(
                seq=seq,
                event_id=str(uuid.uuid4()),
                timestamp=ts,
                action=action,
                subject_id=subject_id,
                purpose=purpose,
                decision=decision,
                detail=safe_detail,
                prev_hash=prev_hash,
                event_hash=event_hash,
            )
            self._events.append(event)
            return event

    def verify(self) -> bool:
        """Return True iff the hash chain is intact."""
        with self._lock:
            prev = self.GENESIS_HASH
            for i, ev in enumerate(self._events):
                if ev.seq != i or ev.prev_hash != prev:
                    return False
                expected = _hash_event(
                    ev.seq, ev.timestamp.isoformat(), ev.action, ev.subject_id,
                    ev.purpose, ev.decision, ev.detail, ev.prev_hash,
                )
                if expected != ev.event_hash:
                    return False
                prev = ev.event_hash
            return True

    def events(self) -> list[AuditEvent]:
        with self._lock:
            return list(self._events)

    def events_for(self, subject_id: str) -> list[AuditEvent]:
        """Return only the events belonging to ``subject_id`` (subject-scoped).

        Used to enforce that a subject with AUDIT_READ can only see its own
        records; cross-subject reads require a separate admin capability.
        """
        with self._lock:
            return [e for e in self._events if e.subject_id == subject_id]

    def __len__(self) -> int:  # pragma: no cover - trivial
        return len(self._events)


class ConsentStore:
    """In-memory registry of consent grants with an attached audit log.

    Fail-closed: :meth:`authorize` raises :class:`ConsentError` unless a live
    grant exists for the (subject, purpose) pair. Every check is audited.
    """

    def __init__(self, audit_log: AuditLog | None = None) -> None:
        self._grants: dict[str, ConsentGrant] = {}
        self.audit = audit_log or AuditLog()
        self._lock = threading.RLock()

    def grant(
        self,
        subject_id: str,
        purpose: Purpose,
        *,
        retention: timedelta = timedelta(days=30),
        at: datetime | None = None,
    ) -> ConsentGrant:
        if not subject_id:
            raise ConsentError("subject_id is required")
        purpose = Purpose(purpose)
        at = at or _utcnow()
        grant = ConsentGrant(
            grant_id=str(uuid.uuid4()),
            subject_id=subject_id,
            purpose=purpose,
            granted_at=at,
            retention=retention,
        )
        with self._lock:
            self._grants[grant.grant_id] = grant
        self.audit.append(
            "consent.grant",
            decision="granted",
            subject_id=subject_id,
            purpose=purpose.value,
            detail={"grant_id": grant.grant_id, "expires_at": grant.expires_at.isoformat()},
            at=at,
        )
        return grant

    def revoke(self, grant_id: str, *, at: datetime | None = None) -> ConsentGrant:
        at = at or _utcnow()
        with self._lock:
            existing = self._grants.get(grant_id)
            if existing is None:
                raise ConsentError(f"unknown grant_id: {grant_id}")
            revoked = ConsentGrant(
                grant_id=existing.grant_id,
                subject_id=existing.subject_id,
                purpose=existing.purpose,
                granted_at=existing.granted_at,
                retention=existing.retention,
                revoked_at=at,
            )
            self._grants[grant_id] = revoked
        self.audit.append(
            "consent.revoke",
            decision="granted",
            subject_id=revoked.subject_id,
            purpose=revoked.purpose.value,
            detail={"grant_id": grant_id},
            at=at,
        )
        return revoked

    def find_active(
        self, subject_id: str, purpose: Purpose, *, at: datetime | None = None
    ) -> ConsentGrant | None:
        at = at or _utcnow()
        purpose = Purpose(purpose)
        with self._lock:
            for grant in self._grants.values():
                if (
                    grant.subject_id == subject_id
                    and grant.purpose == purpose
                    and grant.is_active(at)
                ):
                    return grant
        return None

    def authorize(
        self,
        subject_id: str,
        purpose: Purpose,
        *,
        action: str,
        at: datetime | None = None,
        expected_grant_id: str | None = None,
    ) -> ConsentGrant:
        """Return the live grant or raise :class:`ConsentError` (fail closed).

        Exactly one decision — granted or denied — is appended to the audit log
        per call. If ``expected_grant_id`` is supplied it must match the active
        grant; a mismatch is a single ``denied`` event (never a misleading
        granted→denied pair).
        """
        purpose = Purpose(purpose)
        at = at or _utcnow()
        grant = self.find_active(subject_id, purpose, at=at)
        if grant is None or (
            expected_grant_id is not None and grant.grant_id != expected_grant_id
        ):
            reason = (
                "no active consent grant for purpose"
                if grant is None
                else "grant_id does not match the active grant"
            )
            self.audit.append(
                action,
                decision="denied",
                subject_id=subject_id,
                purpose=purpose.value,
                detail={"reason": reason},
                at=at,
            )
            raise ConsentError(
                f"denied ({reason}) for subject={subject_id!r} purpose={purpose.value!r}"
            )
        self.audit.append(
            action,
            decision="granted",
            subject_id=subject_id,
            purpose=purpose.value,
            detail={"grant_id": grant.grant_id},
            at=at,
        )
        return grant
