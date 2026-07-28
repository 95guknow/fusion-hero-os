"""Public/private data boundary — the ``VaultResolver``.

The public repository (``95guknow/fusion-hero-os``) contains **only**
interfaces, opaque subject identifiers, schemas and synthetic test fixtures.
Real personal data lives exclusively in the private vault repository
(``95guknow/fusion-hero-vault``) and is reached only through a
:class:`VaultResolver` implementation configured out-of-band.

Guarantees
----------
* **Fail closed** — if no vault is configured or authorisation is missing, a
  resolver raises :class:`VaultUnavailableError`/:class:`VaultAuthorizationError`
  rather than returning data or a fabricated default.
* **Opaqueness** — callers pass opaque ``subject_id`` strings; they never carry
  names, emails, device identifiers, MagicDNS names, etc. The graph and audit
  log store only these opaque ids.
* **No leakage** — resolved private attributes are returned to the caller for
  transient use only. Callers MUST NOT write them into graph snapshots or logs;
  the graph layer stores opaque ids and hashes, never raw vault values.
"""

from __future__ import annotations

import hashlib
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from collections.abc import Mapping

PUBLIC_REPO = "95guknow/fusion-hero-os"
VAULT_REPO = "95guknow/fusion-hero-vault"


class VaultError(RuntimeError):
    """Base class for vault boundary errors."""


class VaultUnavailableError(VaultError):
    """Raised when no vault backend is configured (fail closed)."""


class VaultAuthorizationError(VaultError):
    """Raised when the caller is not authorised to resolve a subject."""


@dataclass(frozen=True)
class SubjectRef:
    """An opaque reference to a subject.

    ``subject_id`` is opaque and safe for public storage. ``derive`` produces a
    stable opaque id from a private natural key **without** storing the key.
    """

    subject_id: str

    @staticmethod
    def derive(natural_key: str, *, namespace: str = "fusion-hero") -> SubjectRef:
        digest = hashlib.sha256(f"{namespace}:{natural_key}".encode()).hexdigest()
        return SubjectRef(subject_id=f"subj_{digest[:32]}")


class VaultResolver(ABC):
    """Interface for resolving private attributes for an opaque subject id."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Whether a real vault backend is available."""

    @abstractmethod
    def resolve(self, subject_id: str, *, authorized: bool) -> Mapping[str, object]:
        """Return private attributes for ``subject_id``.

        Implementations MUST raise :class:`VaultUnavailableError` when not
        configured and :class:`VaultAuthorizationError` when ``authorized`` is
        False. They MUST NOT return partial/placeholder personal data.
        """


class NullVaultResolver(VaultResolver):
    """Default resolver used by the public repo: always fails closed.

    This is what ships publicly. It never returns personal data because there
    is none in the public repository. It points operators at the private vault
    repository via configuration.
    """

    def __init__(self, *, vault_repo: str = VAULT_REPO) -> None:
        self.vault_repo = vault_repo

    def is_configured(self) -> bool:
        return False

    def resolve(self, subject_id: str, *, authorized: bool) -> Mapping[str, object]:
        raise VaultUnavailableError(
            "no vault backend configured; private data lives in "
            f"{self.vault_repo!r}. Public repo resolves nothing (fail closed)."
        )


class InMemoryVaultResolver(VaultResolver):
    """A configured resolver backed by an explicit in-memory mapping.

    Intended for tests and local development with **synthetic** data only. It
    still enforces the authorisation gate (fail closed on ``authorized=False``).
    Do not load real personal data into it in the public repository.
    """

    def __init__(self, records: dict[str, Mapping[str, object]] | None = None) -> None:
        self._records: dict[str, Mapping[str, object]] = dict(records or {})

    def put(self, subject_id: str, attributes: Mapping[str, object]) -> None:
        self._records[subject_id] = dict(attributes)

    def is_configured(self) -> bool:
        return True

    def resolve(self, subject_id: str, *, authorized: bool) -> Mapping[str, object]:
        if not authorized:
            raise VaultAuthorizationError(
                f"not authorised to resolve subject {subject_id!r} (fail closed)"
            )
        if subject_id not in self._records:
            raise VaultUnavailableError(f"no vault record for subject {subject_id!r}")
        return dict(self._records[subject_id])


def default_resolver() -> VaultResolver:
    """Return the resolver selected by environment.

    Fail-closed by default: unless ``FUSION_VAULT_BACKEND=memory`` is set for
    local synthetic development, the :class:`NullVaultResolver` is returned.
    There is intentionally no path that auto-loads real data.
    """
    backend = os.getenv("FUSION_VAULT_BACKEND", "null").strip().lower()
    if backend == "memory":
        return InMemoryVaultResolver()
    return NullVaultResolver()
