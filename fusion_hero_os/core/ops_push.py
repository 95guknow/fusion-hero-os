"""
push = public

Git push to known public remote only, after push_layer_guard.
Never includes private vault/secrets (denylist).
"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any

from fusion_hero_os.core.ops_vocabulary import OPS_PUSH, meaning_of

ROOT = Path(__file__).resolve().parents[2]

__all__ = ["push_public", "status"]


def status() -> dict[str, Any]:
    return {
        "ok": True,
        "operation": OPS_PUSH,
        "meaning": meaning_of(OPS_PUSH),
        "german": "öffentlich",
        "guard": "push_layer_guard",
    }


def push_public(
    *,
    remote: str = "origin",
    branch: str | None = None,
    dry: bool = False,
) -> dict[str, Any]:
    """Public push — evaluate guard then git push. deploy/private material excluded by denylist."""
    from fusion_hero_os.core.push_layer_guard import evaluate_push, _load_dotenv_files, load_config

    cfg = load_config()
    dotenv = _load_dotenv_files(cfg)
    d = evaluate_push(remote=remote, branch=branch)
    report: dict[str, Any] = {
        "operation": OPS_PUSH,
        "meaning": "public",
        "allow": d.allow,
        "reason": d.reason,
        "wanted": d.wanted,
        "secret_intent": d.secret_intent,
        "secret_keys_present": d.secret_keys_present,
        "dotenv_loaded": d.dotenv_loaded or dotenv,
        "layers": d.layers_touched,
        "evaluated_at": datetime.now(UTC).isoformat(),
        "dry": dry,
    }
    if not d.allow:
        report["ok"] = False
        report["advice"] = d.advice
        return report

    if dry:
        report["ok"] = True
        report["note"] = "dry-run: public push not executed"
        return report

    br = branch
    if not br:
        br = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=str(ROOT), text=True
        ).strip()
    env = os.environ.copy()
    if d.secret_intent or d.intent:
        env["FUSION_PUSH_INTENT"] = "1"
    cmd = ["git", "push", remote, f"HEAD:{br}"]
    r = subprocess.run(cmd, cwd=str(ROOT), env=env, capture_output=True, text=True)
    report["ok"] = r.returncode == 0
    report["cmd"] = " ".join(cmd)
    report["git_stdout"] = (r.stdout or "")[-500:]
    report["git_stderr"] = (r.stderr or "")[-500:]
    report["exit_code"] = r.returncode

    man = Path.home() / ".fusion" / "ops" / "push_latest.json"
    man.parent.mkdir(parents=True, exist_ok=True)
    man.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["manifest"] = str(man)
    return report


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="push = public")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--branch", default="")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    r = push_public(remote=args.remote, branch=args.branch or None, dry=args.dry)
    print(json.dumps(r, indent=2, ensure_ascii=False))
    return 0 if r.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
