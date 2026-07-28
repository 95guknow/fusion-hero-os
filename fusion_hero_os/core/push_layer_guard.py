"""
Push Layer Guard — weave update structure into layers.

Uses known identifications (remote, branch, VERSION, path→layer, auto-save
markers, intent tokens) to:
  - fail closed on unwanted pushes
  - never block intentional wanted pushes (except hard secret denylist)

Geltung: Spezifikation (guard) · path layering aligned with dual_timeline/layers.
"""
from __future__ import annotations

import fnmatch
import json
import os
import subprocess
from dataclasses import asdict, dataclass, field
from datetime import datetime, UTC
from pathlib import Path
from typing import Any
from collections.abc import Sequence

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "push_layer_guard.yaml"

__all__ = [
    "PushDecision",
    "evaluate_push",
    "load_config",
    "install_hint",
    "status",
]


@dataclass
class PushDecision:
    allow: bool
    reason: str
    wanted: bool
    unwanted: bool
    intent: bool
    auto_save: bool
    remote_ok: bool
    branch: str
    remote: str
    layers_touched: list[str] = field(default_factory=list)
    deny_hits: list[str] = field(default_factory=list)
    soft_deny_hits: list[str] = field(default_factory=list)
    files: list[str] = field(default_factory=list)
    commit_subjects: list[str] = field(default_factory=list)
    platform_ok: bool = True
    advice: str = ""
    secret_intent: bool = False
    secret_keys_present: list[str] = field(default_factory=list)  # names only
    dotenv_loaded: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_config() -> dict[str, Any]:
    if not CONFIG_PATH.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _git(args: Sequence[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        r = subprocess.run(
            ["git", *args],
            cwd=str(cwd or ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:  # noqa: BLE001
        return 1, str(e)


def _match_any(path: str, patterns: list[str]) -> str | None:
    path_n = path.replace("\\", "/")
    while path_n.startswith("./"):
        path_n = path_n[2:]
    base = path_n.split("/")[-1]
    for pat in patterns or []:
        pat_n = pat.replace("\\", "/")
        # basename / exact
        if path_n == pat_n.lstrip("*/") or base == pat_n.lstrip("*/"):
            return pat
        if pat_n.startswith("**/"):
            tail = pat_n[3:]
            if fnmatch.fnmatch(path_n, pat_n) or fnmatch.fnmatch(base, tail) or path_n.endswith("/" + tail) or path_n == tail:
                return pat
        if fnmatch.fnmatch(path_n, pat_n) or fnmatch.fnmatch(base, pat_n):
            return pat
        # prefix style
        if pat_n.endswith("/") and (path_n.startswith(pat_n) or path_n.startswith(pat_n.lstrip("*/"))):
            return pat
        if path_n == pat_n.rstrip("/"):
            return pat
        # *secret* style on full path
        if "*" in pat_n and fnmatch.fnmatch(path_n, pat_n):
            return pat
    return None


def _layers_for_paths(paths: list[str], cfg: dict[str, Any]) -> list[str]:
    layers_cfg = cfg.get("layers") or {}
    touched: list[str] = []
    for path in paths:
        p = path.replace("\\", "/")
        for lid, meta in layers_cfg.items():
            for pref in meta.get("paths") or []:
                pref_n = pref.replace("\\", "/").rstrip("*")
                if pref_n.endswith("/"):
                    if p.startswith(pref_n) or ("/" + pref_n) in ("/" + p):
                        if lid not in touched:
                            touched.append(lid)
                elif fnmatch.fnmatch(p, pref.replace("\\", "/")) or p == pref_n or p.startswith(pref_n.rstrip("/") + "/"):
                    if lid not in touched:
                        touched.append(lid)
    return touched


def _load_dotenv_files(cfg: dict[str, Any]) -> list[str]:
    """Load .env into process env without logging values. Returns loaded path names."""
    si = cfg.get("secret_intent") or {}
    if not si.get("enabled", True) or not si.get("load_dotenv", True):
        return []
    loaded: list[str] = []
    paths = list(si.get("dotenv_paths") or [".env", ".env.local"])
    # operator-local push secret file (never in git)
    paths.append(str(Path.home() / ".fusion" / "secrets" / "push.env"))
    for rel in paths:
        if str(rel).startswith("~") or str(rel).startswith(str(Path.home())):
            path = Path(os.path.expanduser(rel))
        else:
            path = ROOT / rel
        if not path.is_file():
            continue
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                if line.startswith("export "):
                    line = line[7:].strip()
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if not key:
                    continue
                # do not override already-set non-empty env
                if not (os.environ.get(key) or "").strip():
                    os.environ[key] = val
            loaded.append(path.name)
        except Exception:
            continue
    return loaded


def _secret_intent(cfg: dict[str, Any]) -> tuple[bool, list[str]]:
    """Wanted unlock via known secrets (names only returned, never values)."""
    si = cfg.get("secret_intent") or {}
    if not si.get("enabled", True):
        return False, []
    keys = si.get("env_keys_any") or []
    min_present = int(si.get("min_present") or 1)
    present: list[str] = []
    for k in keys:
        val = (os.environ.get(k) or "").strip()
        if val:
            present.append(k)

    # Optional local hash pin for FUSION_PUSH_SECRET
    pin_path = Path(os.path.expanduser(si.get("local_hash_pin") or "~/.fusion/secrets/push_secret.sha256"))
    if si.get("require_hash_pin") and pin_path.is_file():
        secret = (os.environ.get("FUSION_PUSH_SECRET") or "").strip()
        if not secret:
            return False, present
        import hashlib

        digest = hashlib.sha256(secret.encode("utf-8")).hexdigest().strip().lower()
        try:
            expected = pin_path.read_text(encoding="utf-8").strip().lower().split()[0]
        except Exception:
            return False, present
        if digest != expected:
            return False, present
        return True, present + ["hash_pin_ok"]

    if len(present) >= min_present:
        # If pin file exists and FUSION_PUSH_SECRET set, verify when present (optional soft)
        if pin_path.is_file() and (os.environ.get("FUSION_PUSH_SECRET") or "").strip():
            import hashlib

            secret = (os.environ.get("FUSION_PUSH_SECRET") or "").strip()
            digest = hashlib.sha256(secret.encode("utf-8")).hexdigest().strip().lower()
            try:
                expected = pin_path.read_text(encoding="utf-8").strip().lower().split()[0]
                if digest == expected:
                    return True, present + ["hash_pin_ok"]
                # wrong pin — do not grant via this secret alone
                present = [p for p in present if p != "FUSION_PUSH_SECRET"]
                if len(present) < min_present:
                    return False, present
            except Exception:
                pass
        return True, present
    return False, present


def _intent_present(cfg: dict[str, Any], subjects: list[str]) -> bool:
    intent = cfg.get("intent") or {}
    true_vals = {v.lower() for v in (intent.get("env_true_values") or ["1", "true"])}
    for key in intent.get("env_keys") or []:
        val = (os.environ.get(key) or "").strip().lower()
        if val in true_vals:
            return True
    # Secrets-based wanted unlock (operator identity)
    ok_sec, _names = _secret_intent(cfg)
    if ok_sec:
        return True
    markers = intent.get("commit_markers") or []
    prefixes = intent.get("conventional_prefixes") or []
    for sub in subjects:
        s = sub.strip()
        sl = s.lower()
        for m in markers:
            if m.lower() in sl:
                return True
        for pref in prefixes:
            if s.startswith(pref) or sl.startswith(pref.lower()):
                # pure auto-save with conventional? rare — still count as wanted style
                if not any(sl.startswith(ap) for ap in (cfg.get("auto_save") or {}).get("message_prefixes") or []):
                    return True
    return False


def _is_auto_save(subjects: list[str], cfg: dict[str, Any]) -> bool:
    prefixes = (cfg.get("auto_save") or {}).get("message_prefixes") or ["auto-save"]
    if not subjects:
        return False
    # all subjects look like auto-save → auto_save batch
    hits = 0
    for sub in subjects:
        sl = sub.lower().strip()
        if any(sl.startswith(p.lower()) for p in prefixes):
            hits += 1
    return hits == len(subjects) and hits > 0


def _remote_ok(remote_url: str, cfg: dict[str, Any]) -> bool:
    ids = cfg.get("identities") or {}
    allowed = ids.get("remote_urls") or []
    url = (remote_url or "").strip().rstrip("/")
    if not url:
        return False
    for a in allowed:
        a = a.strip().rstrip("/")
        if url == a or url.endswith(a.replace("https://", "").replace("git@", "")):
            return True
        if "95guknow/fusion-hero-os" in url and "95guknow/fusion-hero-os" in a:
            return True
    return False


def _platform_ok(cfg: dict[str, Any]) -> bool:
    ids = cfg.get("identities") or {}
    expected = str(ids.get("platform_version") or "10.0.0")
    vf = ROOT / (ids.get("platform_version_file") or "VERSION")
    if not vf.exists():
        return False
    return vf.read_text(encoding="utf-8").strip() == expected


def _collect_push_files(remote: str, branch: str) -> tuple[list[str], list[str]]:
    """Return (files, commit subjects) for commits not on remote/branch."""
    # commits to be pushed
    code, out = _git(["log", f"{remote}/{branch}..HEAD", "--pretty=%s"])
    if code != 0:
        # no upstream yet — use unpushed vs origin/main or all recent
        code2, out2 = _git(["log", "origin/main..HEAD", "--pretty=%s"])
        subjects = [ln.strip() for ln in (out2 if code2 == 0 else out).splitlines() if ln.strip()]
        code3, out3 = _git(["diff", "--name-only", "origin/main...HEAD"])
        if code3 != 0:
            code3, out3 = _git(["diff", "--name-only", "HEAD~10..HEAD"])
        files = [ln.strip().replace("\\", "/") for ln in out3.splitlines() if ln.strip()]
        return files, subjects

    subjects = [ln.strip() for ln in out.splitlines() if ln.strip()]
    code, out = _git(["diff", "--name-only", f"{remote}/{branch}...HEAD"])
    files = [ln.strip().replace("\\", "/") for ln in out.splitlines() if ln.strip()]
    return files, subjects


def evaluate_push(
    *,
    remote: str = "origin",
    branch: str | None = None,
    remote_url: str | None = None,
    force: bool = False,
    files: list[str] | None = None,
    subjects: list[str] | None = None,
) -> PushDecision:
    cfg = load_config()
    code, cur_branch = _git(["branch", "--show-current"])
    branch = (branch or cur_branch.strip() or "main").strip()

    if not remote_url:
        code, url = _git(["remote", "get-url", remote])
        remote_url = url.strip() if code == 0 else ""

    if files is None or subjects is None:
        f2, s2 = _collect_push_files(remote, branch)
        files = files if files is not None else f2
        subjects = subjects if subjects is not None else s2

    files = [f.replace("\\", "/") for f in (files or [])]
    subjects = list(subjects or [])

    dotenv_loaded = _load_dotenv_files(cfg)
    secret_ok, secret_keys = _secret_intent(cfg)
    intent = _intent_present(cfg, subjects)
    auto_save = _is_auto_save(subjects, cfg)
    remote_ok = _remote_ok(remote_url or "", cfg)
    platform_ok = _platform_ok(cfg)
    layers = _layers_for_paths(files, cfg)

    deny_hits: list[str] = []
    soft_hits: list[str] = []
    for f in files:
        d = _match_any(f, cfg.get("deny_globs") or [])
        if d:
            deny_hits.append(f"{f} ({d})")
        s = _match_any(f, cfg.get("soft_deny_globs") or [])
        if s:
            soft_hits.append(f"{f} ({s})")

    # L6 protected
    if "L6_protected_local" in layers and not intent:
        return PushDecision(
            allow=False,
            reason="L6_protected_local paths require explicit push intent",
            wanted=False,
            unwanted=True,
            intent=intent,
            auto_save=auto_save,
            remote_ok=remote_ok,
            branch=branch,
            remote=remote,
            layers_touched=layers,
            deny_hits=deny_hits,
            soft_deny_hits=soft_hits,
            files=files,
            commit_subjects=subjects,
            platform_ok=platform_ok,
            advice="Set FUSION_PUSH_INTENT=1 or load operator secrets (.env) for wanted push; never commit live inventory.",
            secret_intent=secret_ok,
            secret_keys_present=secret_keys,
            dotenv_loaded=dotenv_loaded,
        )

    if deny_hits:
        return PushDecision(
            allow=False,
            reason="Hard denylist hit (secrets/local inventory) — blocked even with intent",
            wanted=False,
            unwanted=True,
            intent=intent,
            auto_save=auto_save,
            remote_ok=remote_ok,
            branch=branch,
            remote=remote,
            layers_touched=layers,
            deny_hits=deny_hits,
            soft_deny_hits=soft_hits,
            files=files,
            commit_subjects=subjects,
            platform_ok=platform_ok,
            advice="Remove deny_globs matches from the push set.",
            secret_intent=secret_ok,
            secret_keys_present=secret_keys,
            dotenv_loaded=dotenv_loaded,
        )

    if soft_hits and not intent:
        return PushDecision(
            allow=False,
            reason="Soft denylist (large binaries/venv) without push intent",
            wanted=False,
            unwanted=True,
            intent=intent,
            auto_save=auto_save,
            remote_ok=remote_ok,
            branch=branch,
            remote=remote,
            layers_touched=layers,
            deny_hits=deny_hits,
            soft_deny_hits=soft_hits,
            files=files,
            commit_subjects=subjects,
            platform_ok=platform_ok,
            advice="Load operator secrets or set FUSION_PUSH_INTENT=1 if this binary push is wanted.",
            secret_intent=secret_ok,
            secret_keys_present=secret_keys,
            dotenv_loaded=dotenv_loaded,
        )

    _sec = dict(
        secret_intent=secret_ok,
        secret_keys_present=secret_keys,
        dotenv_loaded=dotenv_loaded,
    )

    # God-layer seal: force-push locked until private-person unlock confirmation
    # (surface/docs/conventional commits remain allowed; god-layer force/self-mod blocked)
    try:
        from fusion_hero_os.core.god_layer_seal import is_sealed, require_write

        if is_sealed() and force:
            ok_w, why = require_write(scope="force_push")
            if not ok_w:
                return PushDecision(
                    allow=False,
                    reason=why,
                    wanted=False,
                    unwanted=True,
                    intent=intent,
                    auto_save=auto_save,
                    remote_ok=remote_ok,
                    branch=branch,
                    remote=remote,
                    layers_touched=layers,
                    files=files,
                    commit_subjects=subjects,
                    platform_ok=platform_ok,
                    advice="God-layer sealed for private person. Full read OK. Unlock with confirmation =====stephanhagenurban",
                    **_sec,
                )
    except Exception:
        # Optional integration: a bug or import failure in god_layer_seal
        # must fail open (fall through to the normal branch rules below)
        # rather than blocking every push because of an unrelated error.
        pass

    branch_rules = (cfg.get("branches") or {}).get(branch) or (cfg.get("branches") or {}).get("*") or {}
    if force and branch_rules.get("block_force", True):
        if not intent:
            return PushDecision(
                allow=False,
                reason="Force-push blocked without intent",
                wanted=False,
                unwanted=True,
                intent=intent,
                auto_save=auto_save,
                remote_ok=remote_ok,
                branch=branch,
                remote=remote,
                layers_touched=layers,
                files=files,
                commit_subjects=subjects,
                platform_ok=platform_ok,
                advice="Refusing force-push. Use operator secrets or FUSION_PUSH_INTENT only if truly wanted.",
                **_sec,
            )

    if branch_rules.get("require_identity_remote", True) and not remote_ok:
        return PushDecision(
            allow=False,
            reason=f"Remote URL not in known identities: {remote_url!r}",
            wanted=False,
            unwanted=True,
            intent=intent,
            auto_save=auto_save,
            remote_ok=False,
            branch=branch,
            remote=remote,
            layers_touched=layers,
            files=files,
            commit_subjects=subjects,
            platform_ok=platform_ok,
            advice="Push only to known remote github.com/95guknow/fusion-hero-os",
            **_sec,
        )

    if not platform_ok:
        # warn but allow with intent (version bump mid-flight)
        if not intent:
            return PushDecision(
                allow=False,
                reason="VERSION platform pin mismatch without intent",
                wanted=False,
                unwanted=True,
                intent=intent,
                auto_save=auto_save,
                remote_ok=remote_ok,
                branch=branch,
                remote=remote,
                layers_touched=layers,
                files=files,
                commit_subjects=subjects,
                platform_ok=False,
                advice="Align VERSION to 10.0.0 or unlock with operator secrets / FUSION_PUSH_INTENT.",
                **_sec,
            )

    # auto-save only commits → unwanted on main unless intent (incl. secrets)
    auto_need = bool((cfg.get("auto_save") or {}).get("require_intent_for_push", True))
    if auto_save and auto_need and not intent:
        return PushDecision(
            allow=False,
            reason="Unwanted auto-save push without intent (layer guard)",
            wanted=False,
            unwanted=True,
            intent=False,
            auto_save=True,
            remote_ok=remote_ok,
            branch=branch,
            remote=remote,
            layers_touched=layers,
            files=files,
            commit_subjects=subjects,
            platform_ok=platform_ok,
            advice=(
                "Wanted via secrets: ensure .env has GITHUB_TOKEN / FUSION_PUSH_SECRET / API keys "
                "then: python scripts/wanted_push_via_secrets.py "
                "OR FUSION_PUSH_INTENT=1 OR feat:/[push-ok] commit."
            ),
            **_sec,
        )

    # empty push
    if not files and not subjects:
        return PushDecision(
            allow=True,
            reason="Nothing to push",
            wanted=True,
            unwanted=False,
            intent=intent,
            auto_save=auto_save,
            remote_ok=remote_ok,
            branch=branch,
            remote=remote,
            platform_ok=platform_ok,
            advice="",
            **_sec,
        )

    # wanted path
    why = "Wanted push allowed"
    if secret_ok:
        why = "Wanted push allowed via operator secrets (names only; values never logged)"
    elif intent:
        why = "Wanted push allowed (intent/conventional; known remote; no hard deny)"
    return PushDecision(
        allow=True,
        reason=why,
        wanted=True,
        unwanted=False,
        intent=intent,
        auto_save=auto_save,
        remote_ok=remote_ok,
        branch=branch,
        remote=remote,
        layers_touched=layers,
        deny_hits=deny_hits,
        soft_deny_hits=soft_hits,
        files=files,
        commit_subjects=subjects,
        platform_ok=platform_ok,
        advice="",
        **_sec,
    )


def status() -> dict[str, Any]:
    cfg = load_config()
    code, branch = _git(["branch", "--show-current"])
    code, url = _git(["remote", "get-url", "origin"])
    d = evaluate_push(remote="origin", branch=branch.strip() or "main", remote_url=url.strip())
    return {
        "ok": True,
        "platform": "10.0.0",
        "policy": "pseudo_inhouse_only",
        "freemium": False,
        "config": str(CONFIG_PATH),
        "decision_preview": d.to_dict(),
        "identities": cfg.get("identities"),
        "layers": list((cfg.get("layers") or {}).keys()),
    }


def install_hint() -> str:
    return (
        "python scripts/install_push_guard_hooks.py\n"
        "Wanted push: $env:FUSION_PUSH_INTENT='1'; git push origin main\n"
        "Or commit subject with [push-ok] / feat: / fix: / docs:"
    )


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Push layer guard")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    d = evaluate_push(
        remote=args.remote,
        branch=args.branch or None,
        force=args.force,
    )
    if args.json:
        print(json.dumps(d.to_dict(), indent=2, ensure_ascii=False))
    else:
        mark = "ALLOW" if d.allow else "BLOCK"
        print(f"[{mark}] {d.reason}")
        if d.layers_touched:
            print("layers:", ", ".join(d.layers_touched))
        if d.advice:
            print("advice:", d.advice)
        if d.deny_hits:
            print("deny:", d.deny_hits)
        if d.commit_subjects[:5]:
            print("commits:", d.commit_subjects[:5])
    # write last decision
    out = Path.home() / ".fusion" / "mesh" / "coordination" / "push_guard_last.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = d.to_dict()
    payload["evaluated_at"] = datetime.now(UTC).isoformat()
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0 if d.allow else 2


if __name__ == "__main__":
    raise SystemExit(main())
