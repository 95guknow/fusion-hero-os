# -*- coding: utf-8 -*-
"""Bottom-up fan-out: all instances + Horkruxe — Fusion Hero OS v12.1.0"""
from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "horkrux_instances.yaml"
PLATFORM = "12.1.0"
DOCS = ROOT / "docs" / "ops" / "HORKRUX_BOTTOM_UP.latest.json"

__all__ = ["load_config", "run_bottom_up", "status"]


def load_config() -> Dict[str, Any]:
    if not CONFIG.exists():
        return {}
    try:
        import yaml

        return yaml.safe_load(CONFIG.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def _expand(p: str) -> Path:
    return Path(os.path.expanduser(str(p).replace("\\", "/")))


def _git(cwd: Path, *args: str) -> Tuple[int, str, str]:
    r = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return r.returncode, (r.stdout or "").strip(), (r.stderr or "").strip()


def _is_git(path: Path) -> bool:
    return path.exists() and (path / ".git").exists()


def _sync_git(entry: Dict[str, Any], kanon_tip: Optional[str]) -> Dict[str, Any]:
    path = _expand(str(entry.get("path") or ""))
    branch = entry.get("branch") or "main"
    optional = bool(entry.get("optional"))
    iid = entry.get("id") or path.name
    out: Dict[str, Any] = {
        "id": iid,
        "kind": "git",
        "path": str(path),
        "branch": branch,
        "role": entry.get("role"),
        "layer": entry.get("_layer"),
    }
    if not path.exists():
        out.update({"ok": optional, "skipped": True, "reason": "path_missing"})
        return out
    if not _is_git(path):
        out.update({"ok": optional, "skipped": True, "reason": "not_git"})
        return out
    dirty_code, dirty_out, _ = _git(path, "status", "--porcelain")
    dirty = bool(dirty_out.strip()) if dirty_code == 0 else None
    _git(path, "fetch", "--all", "--prune")
    c, _, _ = _git(path, "rev-parse", "--verify", branch)
    if c == 0:
        _git(path, "checkout", branch)
    if dirty:
        _git(path, "stash", "push", "-u", "-m", f"horkrux-bottom-up-{PLATFORM}")
        out["stashed"] = True
    pcode, _, perr = _git(path, "pull", "--ff-only")
    if pcode != 0:
        pcode, _, perr = _git(path, "pull")
    tcode, tip, _ = _git(path, "rev-parse", "--short", "HEAD")
    ver = None
    vf = path / "VERSION"
    if vf.exists():
        ver = vf.read_text(encoding="utf-8").strip()
    out.update(
        {
            "ok": pcode == 0,
            "tip": tip if tcode == 0 else None,
            "version": ver,
            "was_dirty": dirty,
            "stderr": perr[-200:],
            "matches_kanon_tip": (tip == kanon_tip) if (tip and kanon_tip) else None,
            "version_ok": (ver == PLATFORM) if ver and entry.get("expect_version_file") else None,
        }
    )
    return out


def _check_state_dir(entry: Dict[str, Any]) -> Dict[str, Any]:
    path = _expand(str(entry.get("path") or ""))
    optional = bool(entry.get("optional"))
    exists = path.exists()
    n = 0
    if exists:
        try:
            n = sum(1 for _ in path.rglob("*") if _.is_file())
        except Exception:
            n = -1
    return {
        "id": entry.get("id"),
        "kind": "state_dir",
        "path": str(path),
        "role": entry.get("role"),
        "layer": entry.get("_layer"),
        "ok": exists or optional,
        "exists": exists,
        "file_count": n,
        "skipped": (not exists) and optional,
    }


def _check_skill(entry: Dict[str, Any], platform: str) -> Dict[str, Any]:
    path = _expand(str(entry.get("path") or ""))
    optional = bool(entry.get("optional"))
    if not path.exists():
        return {
            "id": entry.get("id"),
            "kind": "skill_dir",
            "ok": optional,
            "skipped": True,
            "reason": "path_missing",
            "path": str(path),
            "layer": entry.get("_layer"),
        }
    skill, sync = path / "SKILL.md", path / "GITHUB_SYNC.json"
    pin = None
    if sync.exists():
        try:
            pin = json.loads(sync.read_text(encoding="utf-8"))
        except Exception:
            pin = None
    txt = skill.read_text(encoding="utf-8", errors="replace")[:8000] if skill.exists() else ""
    return {
        "id": entry.get("id"),
        "kind": "skill_dir",
        "path": str(path),
        "role": entry.get("role"),
        "layer": entry.get("_layer"),
        "ok": True,
        "has_skill_md": skill.exists(),
        "has_github_sync": sync.exists(),
        "github_sync_platform": (pin or {}).get("platform_version")
        or (pin or {}).get("FUSION_PLATFORM_VERSION"),
        "skill_mentions_v12": ("12.1.0" in txt or "12.0.0" in txt or "v12" in txt),
        "target_platform": platform,
    }


def _check_remote(entry: Dict[str, Any], kanon_full: Optional[str]) -> Dict[str, Any]:
    repo = _expand(str(entry.get("repo_path") or ROOT))
    remote = entry.get("remote") or "origin"
    ref = entry.get("ref") or "refs/heads/main"
    code, out, err = _git(repo, "ls-remote", remote, ref)
    sha = out.split()[0] if out else None
    return {
        "id": entry.get("id"),
        "kind": "remote_check",
        "remote": remote,
        "ref": ref,
        "role": entry.get("role"),
        "layer": entry.get("_layer"),
        "ok": code == 0 and bool(sha),
        "sha": sha,
        "short": (sha[:7] if sha else None),
        "matches_local_kanon": (sha == kanon_full)
        if (sha and kanon_full and "heads/main" in ref)
        else None,
        "stderr": err[-120:] if code != 0 else "",
    }


def _scan_worktree_root(entry: Dict[str, Any], kanon_tip: Optional[str]) -> Dict[str, Any]:
    path = _expand(str(entry.get("path") or ""))
    optional = bool(entry.get("optional"))
    if not path.exists():
        return {
            "id": entry.get("id"),
            "kind": "path",
            "ok": optional,
            "skipped": True,
            "reason": "path_missing",
            "path": str(path),
        }
    found: List[Dict[str, Any]] = []
    candidates = [path]
    wt = path / ".worktrees"
    if wt.is_dir():
        candidates.extend([p for p in wt.iterdir() if p.is_dir()])
    if path.is_dir():
        for p in path.iterdir():
            if p.is_dir() and (p / ".git").exists():
                candidates.append(p)
    seen = set()
    for p in candidates:
        sp = str(p)
        if sp in seen:
            continue
        seen.add(sp)
        if _is_git(p):
            _git(p, "fetch", "--all", "--prune")
            tcode, tip, _ = _git(p, "rev-parse", "--short", "HEAD")
            found.append(
                {
                    "id": f"scan:{p.name}",
                    "path": sp,
                    "tip": tip if tcode == 0 else None,
                    "ok": True,
                    "matches_kanon_tip": (tip == kanon_tip) if tip and kanon_tip else None,
                }
            )
    return {
        "id": entry.get("id"),
        "kind": "path_scan",
        "path": str(path),
        "ok": True,
        "scanned_git_dirs": len(found),
        "children": found[:40],
        "layer": "L2_worktrees",
    }


def _preserve_horcrux(payload: Dict[str, Any]) -> Dict[str, Any]:
    store = _expand("~/.fusion/horcrux/bottom_up_v12")
    store.mkdir(parents=True, exist_ok=True)
    try:
        from fusion_hero_os.core.pseudo_horcrux import PseudoHorcruxStore

        ph = PseudoHorcruxStore(store)
        gen = ph.preserve(payload)
        return {"ok": True, "store": str(store), "result": gen}
    except Exception as e:  # noqa: BLE001
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        jp = store / f"bottom_up_{ts}.json"
        jp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return {"ok": True, "store": str(store), "fallback_json": str(jp), "note": str(e)[:160]}


def run_bottom_up(*, sync_grok: bool = True) -> Dict[str, Any]:
    cfg = load_config()
    layers = cfg.get("layers") or {}
    t0 = datetime.now(timezone.utc)
    kcode, kanon_tip, _ = _git(ROOT, "rev-parse", "--short", "HEAD")
    kcode2, kanon_full, _ = _git(ROOT, "rev-parse", "HEAD")
    ver = (
        (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        if (ROOT / "VERSION").exists()
        else PLATFORM
    )
    results: List[Dict[str, Any]] = []
    for layer_name in [
        "L0_state",
        "L1_instances",
        "L2_worktrees",
        "L3_skills_horkruxe",
        "L4_remotes",
    ]:
        for entry in layers.get(layer_name) or []:
            entry = dict(entry)
            entry["_layer"] = layer_name
            kind = entry.get("kind")
            if kind == "state_dir":
                results.append(_check_state_dir(entry))
            elif kind == "git":
                results.append(_sync_git(entry, kanon_tip if kcode == 0 else None))
            elif kind == "skill_dir":
                results.append(_check_skill(entry, ver))
            elif kind == "remote_check":
                results.append(_check_remote(entry, kanon_full if kcode2 == 0 else None))
            elif kind == "path":
                results.append(_scan_worktree_root(entry, kanon_tip if kcode == 0 else None))
            else:
                results.append(
                    {"id": entry.get("id"), "ok": False, "reason": f"unknown_kind:{kind}"}
                )
    if sync_grok:
        script = ROOT / "sync_grok_intern.ps1"
        if script.exists():
            r = subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-File",
                    str(script),
                ],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            results.append(
                {
                    "id": "sync_grok_intern",
                    "kind": "script",
                    "layer": "L3_skills_horkruxe",
                    "ok": r.returncode == 0,
                    "stdout_tail": (r.stdout or "")[-400:],
                }
            )
    try:
        from fusion_hero_os.core.daycycle_mem import fanout_updates

        dc = fanout_updates()
        results.append(
            {"id": "daycycle_fanout", "kind": "daycycle", "layer": "L1_instances", **dc}
        )
    except Exception as e:  # noqa: BLE001
        results.append({"id": "daycycle_fanout", "ok": False, "error": str(e)[:160]})

    ok_flags = [bool(r.get("ok")) for r in results if not r.get("skipped")]
    payload = {
        "platform": ver,
        "kanon_tip": kanon_tip if kcode == 0 else None,
        "fanout_ok": all(ok_flags) if ok_flags else False,
        "utc": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "total": len(results),
            "ok": sum(1 for r in results if r.get("ok") and not r.get("skipped")),
            "skipped": sum(1 for r in results if r.get("skipped")),
            "fail": sum(1 for r in results if (not r.get("ok")) and not r.get("skipped")),
        },
    }
    horcrux = _preserve_horcrux(payload)
    report = {
        "kind": "HORKRUX_BOTTOM_UP",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform_target": PLATFORM,
        "platform_version_file": ver,
        "kanon_tip": kanon_tip if kcode == 0 else None,
        "duration_sec": round((datetime.now(timezone.utc) - t0).total_seconds(), 2),
        "ok": payload["fanout_ok"],
        "counts": payload["counts"],
        "results": results,
        "pseudo_horcrux": horcrux,
        "geltung": "path/git results = Satz · missing optional = Bedingt skip",
    }
    DOCS.parent.mkdir(parents=True, exist_ok=True)
    DOCS.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    pin = Path.home() / ".fusion" / "ops" / "horkrux_bottom_up.latest.json"
    pin.parent.mkdir(parents=True, exist_ok=True)
    pin.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["docs"] = str(DOCS)
    report["pin"] = str(pin)
    return report


def status() -> Dict[str, Any]:
    return {
        "ok": True,
        "platform": PLATFORM,
        "config": str(CONFIG),
        "docs": str(DOCS) if DOCS.exists() else None,
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Bottom-up all instances + horkruxe")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--no-grok", action="store_true")
    args = ap.parse_args()
    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    r = run_bottom_up(sync_grok=not args.no_grok)
    compact = {
        "ok": r.get("ok"),
        "platform": r.get("platform_version_file"),
        "kanon_tip": r.get("kanon_tip"),
        "counts": r.get("counts"),
        "duration_sec": r.get("duration_sec"),
        "docs": r.get("docs"),
        "fail_ids": [
            x.get("id")
            for x in r.get("results") or []
            if not x.get("ok") and not x.get("skipped")
        ],
    }
    print(json.dumps(compact, indent=2, ensure_ascii=False))
    for x in r.get("results") or []:
        flag = "SKIP" if x.get("skipped") else ("OK" if x.get("ok") else "FAIL")
        print(
            f"  [{flag}] {x.get('layer', '?')} {x.get('id')} tip={x.get('tip')} ver={x.get('version')}"
        )
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
