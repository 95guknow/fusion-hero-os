# -*- coding: utf-8 -*-
"""
Daycycle Mem + Central Consolidation — Fusion Hero OS v12.1.0

- Minute: append day-schedule line to local mem.md
- Hourly: flush mem.md → private repo `dev` (commit+push), then clear mem.md
- Every 4h: open/update PR dev → main (private repo)
- Daily: merge PR to top + fan-out git pull to registered instances
- Instances log real-world traffic to local jsonl (normal logging)
- Agent: protocol-only unless operator wake word "testtest"

Honesty:
  - Does not push mem to public fusion-hero-os
  - Does not invent remote PR success if gh fails
  - Fan-out only touches paths that exist
  - Redacts common secret patterns from mem lines

Geltung: file/git results = Satz · schedule language = Spezifikation
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import socket
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[2]
PLATFORM = "12.1.0"
CONFIG_PATH = ROOT / "daycycle_mem.yaml"

__all__ = [
    "load_config",
    "status",
    "minute_tick",
    "hourly_flush",
    "pr_cycle",
    "daily_top_merge",
    "fanout_updates",
    "log_instance_traffic",
    "protocol_event",
    "is_agent_awake",
    "wake_agent",
    "run_due",
]


def load_config() -> Dict[str, Any]:
    cfg: Dict[str, Any] = {}
    if CONFIG_PATH.exists():
        try:
            import yaml

            cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")) or {}
        except Exception:
            cfg = {}
    override = Path(os.path.expanduser((cfg.get("paths") or {}).get("config_override") or "~/.fusion/daycycle/config.json"))
    if override.exists():
        try:
            ov = json.loads(override.read_text(encoding="utf-8"))
            if isinstance(ov, dict):
                cfg = _deep_merge(cfg, ov)
        except Exception:
            pass
    return cfg


def _deep_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _cfg() -> Dict[str, Any]:
    return load_config()


def _p(key: str, default: str) -> Path:
    raw = ((_cfg().get("paths") or {}).get(key) or default)
    p = Path(os.path.expanduser(raw))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def mem_path() -> Path:
    return _p("local_mem", "~/.fusion/daycycle/mem.md")


def state_path() -> Path:
    return _p("local_state", "~/.fusion/daycycle/state.json")


def traffic_path() -> Path:
    return _p("local_traffic_log", "~/.fusion/daycycle/instance_traffic.jsonl")


def protocol_path() -> Path:
    return _p("local_protocol", "~/.fusion/daycycle/agent_protocol.jsonl")


def archive_dir() -> Path:
    p = _p("local_archive", "~/.fusion/daycycle/archive")
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_state() -> Dict[str, Any]:
    sp = state_path()
    if sp.exists():
        try:
            return json.loads(sp.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {
        "platform": PLATFORM,
        "last_minute": None,
        "last_hourly_flush": None,
        "last_pr": None,
        "last_daily_merge": None,
        "last_fanout": None,
        "agent_wake_until": None,
        "minute_count": 0,
        "flush_count": 0,
    }


def save_state(st: Dict[str, Any]) -> None:
    st["updated_at"] = datetime.now(timezone.utc).isoformat()
    st["platform"] = PLATFORM
    state_path().write_text(json.dumps(st, indent=2, ensure_ascii=False), encoding="utf-8")


def _now_local() -> datetime:
    return datetime.now().astimezone()


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _redact(text: str) -> str:
    pats = (_cfg().get("mem") or {}).get("redact_patterns") or []
    out = text
    for pat in pats:
        try:
            out = re.sub(pat, "[REDACTED]", out)
        except re.error:
            continue
    return out


def _git(cwd: Path, *args: str, check: bool = False) -> Tuple[int, str, str]:
    r = subprocess.run(
        ["git", *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {r.stderr[:300]}")
    return r.returncode, r.stdout or "", r.stderr or ""


def _gh(*args: str) -> Tuple[int, str, str]:
    r = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return r.returncode, r.stdout or "", r.stderr or ""


def private_repo_path() -> Path:
    pr = _cfg().get("private_repo") or {}
    return Path(pr.get("local_path") or r"C:\Users\Admin\fusion-hero-os-daily-plans")


def ensure_dev_branch() -> Dict[str, Any]:
    """Ensure private repo exists and `dev` branch is present."""
    repo = private_repo_path()
    if not repo.exists():
        return {"ok": False, "error": f"private repo path missing: {repo}"}
    pr = _cfg().get("private_repo") or {}
    dev = pr.get("branch_dev") or "dev"
    top = pr.get("branch_top") or "main"
    code, out, err = _git(repo, "rev-parse", "--is-inside-work-tree")
    if code != 0:
        return {"ok": False, "error": "not a git repo", "stderr": err[:160]}
    _git(repo, "fetch", pr.get("remote") or "origin")
    # create dev from main if missing
    code, _, _ = _git(repo, "show-ref", "--verify", f"refs/heads/{dev}")
    if code != 0:
        _git(repo, "checkout", top)
        _git(repo, "pull", pr.get("remote") or "origin", top)
        _git(repo, "checkout", "-B", dev)
        _git(repo, "push", "-u", pr.get("remote") or "origin", dev)
    else:
        _git(repo, "checkout", dev)
        # best-effort sync
        _git(repo, "pull", pr.get("remote") or "origin", dev)
    return {"ok": True, "repo": str(repo), "branch": dev}


# ---------------------------------------------------------------------------
# Agent protocol (passive unless testtest)
# ---------------------------------------------------------------------------

def protocol_event(kind: str, message: str, *, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Always-on protocol log (passive)."""
    rec = {
        "ts": _now_utc().isoformat(),
        "kind": kind,
        "message": _redact(message)[:2000],
        "meta": meta or {},
        "platform": PLATFORM,
        "agent_mode": "protocol_only" if not is_agent_awake() else "awake",
    }
    path = protocol_path()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


def is_agent_awake() -> bool:
    st = load_state()
    until = st.get("agent_wake_until")
    if not until:
        return False
    try:
        t = datetime.fromisoformat(until.replace("Z", "+00:00"))
        return _now_utc() < t.astimezone(timezone.utc)
    except Exception:
        return False


def wake_agent(source: str = "operator") -> Dict[str, Any]:
    """Activate engagement window after explicit wake word."""
    ap = _cfg().get("agent_protocol") or {}
    ttl = int(ap.get("wake_ttl_minutes") or 30)
    until = datetime.fromtimestamp(time.time() + ttl * 60, tz=timezone.utc)
    st = load_state()
    st["agent_wake_until"] = until.isoformat()
    st["agent_wake_source"] = source
    save_state(st)
    return protocol_event("wake", f"agent awake for {ttl}m", meta={"until": until.isoformat(), "source": source})


def check_wake_word(text: str) -> bool:
    ap = _cfg().get("agent_protocol") or {}
    word = str(ap.get("wake_word") or "testtest").strip().lower()
    if word and word in (text or "").lower():
        wake_agent(source="wake_word")
        return True
    return False


# ---------------------------------------------------------------------------
# Minute tick → mem.md
# ---------------------------------------------------------------------------

def minute_tick(*, note: str = "", traffic_hint: str = "") -> Dict[str, Any]:
    """Append one minute line to local mem.md (day schedule)."""
    cfg = _cfg()
    mem_cfg = cfg.get("mem") or {}
    now = _now_local()
    st = load_state()
    host = socket.gethostname() if mem_cfg.get("include_hostname", True) else "-"
    ver = PLATFORM if mem_cfg.get("include_platform_version", True) else "-"
    line = (
        f"- [{now.strftime('%Y-%m-%d %H:%M:%S %z')}] "
        f"host={host} platform={ver} "
        f"note={_redact(note or 'daycycle-minute')} "
        f"traffic={_redact(traffic_hint or 'instance-traffic-see-jsonl')}"
    )
    path = mem_path()
    if not path.exists():
        header = (
            f"# Daycycle mem — Fusion Hero OS {PLATFORM}\n"
            f"# Local minute log · flushed hourly to private repo dev · then cleared\n"
            f"# Started: {now.isoformat()}\n\n"
        )
        path.write_text(header, encoding="utf-8")
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    st["last_minute"] = now.isoformat()
    st["minute_count"] = int(st.get("minute_count") or 0) + 1
    save_state(st)
    protocol_event("minute_tick", line[:240])
    # force flush if huge
    lines = path.read_text(encoding="utf-8", errors="replace").count("\n")
    max_lines = int(mem_cfg.get("max_lines_before_force_flush") or 5000)
    forced = False
    if lines >= max_lines:
        hourly_flush(reason="force_max_lines")
        forced = True
    return {"ok": True, "path": str(path), "line": line, "lines": lines, "forced_flush": forced}


# ---------------------------------------------------------------------------
# Hourly flush → private dev
# ---------------------------------------------------------------------------

def hourly_flush(*, reason: str = "hourly") -> Dict[str, Any]:
    """Commit current mem.md to private repo branch dev, push, archive, clear local mem."""
    cfg = _cfg()
    pr = cfg.get("private_repo") or {}
    dev = pr.get("branch_dev") or "dev"
    remote = pr.get("remote") or "origin"
    prefix = pr.get("commit_prefix") or "daycycle:"
    mem_dir_rel = pr.get("mem_dir") or "daycycle/mem"

    ensure = ensure_dev_branch()
    if not ensure.get("ok"):
        return {"ok": False, "step": "ensure_dev", **ensure}

    repo = private_repo_path()
    path = mem_path()
    content = path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    if not content.strip() or content.count("\n") < 3:
        # still record heartbeat file
        content = content or f"# empty flush {_now_utc().isoformat()}\n"

    now = _now_local()
    stamp = now.strftime("%Y%m%d_%H%M%S")
    # archive local copy
    arch = archive_dir() / f"mem_{stamp}.md"
    arch.write_text(content, encoding="utf-8")

    # write into private repo
    dest_dir = repo / mem_dir_rel
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"mem_{stamp}.md"
    dest.write_text(content, encoding="utf-8")
    # rolling latest
    (dest_dir / "mem_latest.md").write_text(content, encoding="utf-8")
    (dest_dir / "LAST_FLUSH.json").write_text(
        json.dumps(
            {
                "flushed_at": _now_utc().isoformat(),
                "reason": reason,
                "bytes": len(content.encode("utf-8")),
                "sha16": hashlib.sha256(content.encode("utf-8")).hexdigest()[:16],
                "platform": PLATFORM,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    _git(repo, "checkout", dev)
    _git(repo, "add", mem_dir_rel)
    msg = f"{prefix} hourly mem flush {stamp} [{reason}] platform={PLATFORM}"
    code, out, err = _git(repo, "commit", "-m", msg)
    committed = code == 0
    # push
    pcode, pout, perr = _git(repo, "push", remote, dev)
    pushed = pcode == 0

    # clear local mem (header only)
    path.write_text(
        f"# Daycycle mem — Fusion Hero OS {PLATFORM}\n"
        f"# Cleared after flush {now.isoformat()} reason={reason}\n"
        f"# Next lines accumulate until next hourly flush\n\n",
        encoding="utf-8",
    )

    st = load_state()
    st["last_hourly_flush"] = _now_utc().isoformat()
    st["flush_count"] = int(st.get("flush_count") or 0) + 1
    st["last_flush_push_ok"] = pushed
    st["last_flush_commit_ok"] = committed
    save_state(st)
    protocol_event(
        "hourly_flush",
        f"committed={committed} pushed={pushed} dest={dest.name}",
        meta={"reason": reason, "sha16": hashlib.sha256(content.encode()).hexdigest()[:16]},
    )
    return {
        "ok": committed and pushed,
        "committed": committed,
        "pushed": pushed,
        "commit_stdout": out[-200:],
        "commit_stderr": err[-200:],
        "push_stderr": perr[-200:],
        "archive": str(arch),
        "dest": str(dest),
        "branch": dev,
        "reason": reason,
    }


# ---------------------------------------------------------------------------
# 4h PR cycle
# ---------------------------------------------------------------------------

def pr_cycle() -> Dict[str, Any]:
    """Open or refresh PR from private dev → main."""
    cfg = _cfg()
    pr = cfg.get("private_repo") or {}
    owner = pr.get("owner") or "95guknow"
    name = pr.get("name") or "fusion-hero-os-daily-plans"
    dev = pr.get("branch_dev") or "dev"
    top = pr.get("branch_top") or "main"
    ensure = ensure_dev_branch()
    if not ensure.get("ok"):
        return {"ok": False, "step": "ensure_dev", **ensure}

    # list open PRs
    code, out, err = _gh(
        "pr", "list",
        "--repo", f"{owner}/{name}",
        "--base", top,
        "--head", dev,
        "--state", "open",
        "--json", "number,url,title",
    )
    existing = []
    if code == 0 and out.strip():
        try:
            existing = json.loads(out)
        except Exception:
            existing = []

    if existing:
        pr_info = existing[0]
        st = load_state()
        st["last_pr"] = _now_utc().isoformat()
        st["last_pr_number"] = pr_info.get("number")
        st["last_pr_url"] = pr_info.get("url")
        save_state(st)
        protocol_event("pr_refresh", f"existing PR #{pr_info.get('number')}", meta=pr_info)
        return {"ok": True, "action": "existing", "pr": pr_info}

    title = f"daycycle: dev → {top} consolidation ({PLATFORM})"
    body = (
        f"## Daycycle PR\n\n"
        f"Platform **{PLATFORM}** · BIG ALPHA\n\n"
        f"- Hourly mem flushes on `{dev}`\n"
        f"- 4h PR cycle\n"
        f"- Daily top merge + instance fan-out\n\n"
        f"Private repo only. No vault secrets.\n"
    )
    code, out, err = _gh(
        "pr", "create",
        "--repo", f"{owner}/{name}",
        "--base", top,
        "--head", dev,
        "--title", title,
        "--body", body,
    )
    ok = code == 0
    st = load_state()
    st["last_pr"] = _now_utc().isoformat()
    st["last_pr_create_ok"] = ok
    st["last_pr_stdout"] = out[-300:]
    st["last_pr_stderr"] = err[-300:]
    # try parse URL
    url = out.strip().splitlines()[-1] if out.strip() else ""
    if url.startswith("http"):
        st["last_pr_url"] = url
    save_state(st)
    protocol_event("pr_create", f"ok={ok} {url or err[:120]}")
    return {"ok": ok, "action": "create", "stdout": out[-400:], "stderr": err[-400:], "url": url}


# ---------------------------------------------------------------------------
# Daily top merge + fanout
# ---------------------------------------------------------------------------

def daily_top_merge() -> Dict[str, Any]:
    """Merge open daycycle PR into private main (top)."""
    cfg = _cfg()
    pr = cfg.get("private_repo") or {}
    owner = pr.get("owner") or "95guknow"
    name = pr.get("name") or "fusion-hero-os-daily-plans"
    top = pr.get("branch_top") or "main"
    dev = pr.get("branch_dev") or "dev"

    # find PR
    code, out, err = _gh(
        "pr", "list",
        "--repo", f"{owner}/{name}",
        "--base", top,
        "--head", dev,
        "--state", "open",
        "--json", "number,url",
    )
    prs = []
    if code == 0 and out.strip():
        try:
            prs = json.loads(out)
        except Exception:
            prs = []
    if not prs:
        # try merge locally dev into main
        repo = private_repo_path()
        _git(repo, "fetch", pr.get("remote") or "origin")
        _git(repo, "checkout", top)
        _git(repo, "pull", pr.get("remote") or "origin", top)
        mcode, mout, merr = _git(repo, "merge", "--no-ff", dev, "-m", f"daycycle: daily top merge {PLATFORM}")
        pcode, pout, perr = _git(repo, "push", pr.get("remote") or "origin", top)
        ok = mcode == 0 and pcode == 0
        st = load_state()
        st["last_daily_merge"] = _now_utc().isoformat()
        st["last_daily_merge_ok"] = ok
        st["last_daily_merge_mode"] = "local_merge"
        save_state(st)
        protocol_event("daily_merge", f"local_merge ok={ok}")
        return {
            "ok": ok,
            "mode": "local_merge",
            "merge_stderr": merr[-200:],
            "push_stderr": perr[-200:],
        }

    number = prs[0]["number"]
    code, out, err = _gh(
        "pr", "merge", str(number),
        "--repo", f"{owner}/{name}",
        "--merge",
        "--delete-branch=false",
    )
    ok = code == 0
    st = load_state()
    st["last_daily_merge"] = _now_utc().isoformat()
    st["last_daily_merge_ok"] = ok
    st["last_daily_merge_mode"] = "gh_pr_merge"
    st["last_daily_merge_pr"] = number
    st["last_daily_merge_stderr"] = err[-300:]
    save_state(st)
    protocol_event("daily_merge", f"pr_merge #{number} ok={ok}")
    # recreate dev from main for next cycle
    if ok:
        repo = private_repo_path()
        _git(repo, "fetch", pr.get("remote") or "origin")
        _git(repo, "checkout", top)
        _git(repo, "pull", pr.get("remote") or "origin", top)
        _git(repo, "checkout", "-B", dev)
        _git(repo, "push", pr.get("remote") or "origin", dev, "--force-with-lease")
    return {"ok": ok, "mode": "gh_pr_merge", "number": number, "stdout": out[-300:], "stderr": err[-300:]}


def fanout_updates() -> Dict[str, Any]:
    """Pull latest updates on all registered instance paths (bottom-up fan-out)."""
    cfg = _cfg()
    instances = cfg.get("instances") or []
    results: List[Dict[str, Any]] = []
    for inst in instances:
        path = Path(inst.get("path") or "")
        branch = inst.get("branch") or "main"
        optional = bool(inst.get("optional"))
        iid = inst.get("id") or path.name
        if not path.exists():
            results.append({"id": iid, "ok": optional, "skipped": True, "reason": "path_missing"})
            continue
        if not (path / ".git").exists() and not (path / ".git").is_file():
            # worktree git file
            results.append({"id": iid, "ok": optional, "skipped": True, "reason": "not_git"})
            continue
        _git(path, "fetch", "--all", "--prune")
        # checkout branch if exists
        code, _, _ = _git(path, "rev-parse", "--verify", branch)
        if code == 0:
            _git(path, "checkout", branch)
        pcode, pout, perr = _git(path, "pull", "--ff-only")
        # fallback pull
        if pcode != 0:
            pcode, pout, perr = _git(path, "pull")
        tip_code, tip, _ = _git(path, "rev-parse", "--short", "HEAD")
        results.append(
            {
                "id": iid,
                "ok": pcode == 0,
                "branch": branch,
                "tip": tip.strip() if tip_code == 0 else None,
                "stderr": perr[-160:],
                "role": inst.get("role"),
            }
        )
    st = load_state()
    st["last_fanout"] = _now_utc().isoformat()
    st["last_fanout_results"] = results
    save_state(st)
    protocol_event("fanout", f"instances={len(results)}", meta={"results": results})
    return {"ok": all(r.get("ok") or r.get("skipped") for r in results), "results": results}


# ---------------------------------------------------------------------------
# Instance traffic log (normal logging)
# ---------------------------------------------------------------------------

def log_instance_traffic(
    instance_id: str,
    *,
    direction: str = "egress",
    dest: str = "",
    bytes_n: int = 0,
    note: str = "",
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Instances log real-world traffic normally (local jsonl)."""
    rec = {
        "ts": _now_utc().isoformat(),
        "instance_id": instance_id,
        "direction": direction,
        "dest": _redact(dest)[:300],
        "bytes": int(bytes_n),
        "note": _redact(note)[:500],
        "meta": meta or {},
        "host": socket.gethostname(),
        "platform": PLATFORM,
    }
    path = traffic_path()
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return rec


# ---------------------------------------------------------------------------
# Scheduler: run whatever is due
# ---------------------------------------------------------------------------

def run_due(*, force: Optional[str] = None) -> Dict[str, Any]:
    """
    Run due daycycle steps.
    force: minute|hourly|pr|daily|fanout|all
    """
    st = load_state()
    now = _now_local()
    out: Dict[str, Any] = {"ok": True, "ran": [], "platform": PLATFORM, "now": now.isoformat()}

    def _due_hourly() -> bool:
        last = st.get("last_hourly_flush")
        if not last:
            return True
        try:
            t = datetime.fromisoformat(last.replace("Z", "+00:00"))
            return (_now_utc() - t.astimezone(timezone.utc)).total_seconds() >= 3600
        except Exception:
            return True

    def _due_pr() -> bool:
        hours = float((_cfg().get("schedule") or {}).get("pr_every_hours") or 4)
        last = st.get("last_pr")
        if not last:
            return True
        try:
            t = datetime.fromisoformat(last.replace("Z", "+00:00"))
            return (_now_utc() - t.astimezone(timezone.utc)).total_seconds() >= hours * 3600
        except Exception:
            return True

    def _due_daily() -> bool:
        hour = int((_cfg().get("schedule") or {}).get("daily_top_merge_hour_local") or 3)
        last = st.get("last_daily_merge")
        # once per local calendar day after configured hour
        if now.hour < hour:
            return False
        if not last:
            return True
        try:
            t = datetime.fromisoformat(last.replace("Z", "+00:00")).astimezone()
            return t.date() < now.date()
        except Exception:
            return True

    # always minute unless force something else exclusively
    if force in (None, "minute", "all"):
        out["ran"].append({"step": "minute", "result": minute_tick()})

    if force in ("hourly", "all") or (force is None and _due_hourly()):
        out["ran"].append({"step": "hourly", "result": hourly_flush()})

    if force in ("pr", "all") or (force is None and _due_pr()):
        out["ran"].append({"step": "pr", "result": pr_cycle()})

    if force in ("daily", "all") or (force is None and _due_daily()):
        merge_r = daily_top_merge()
        out["ran"].append({"step": "daily", "result": merge_r})
        if (_cfg().get("schedule") or {}).get("daily_fanout_after_merge", True):
            out["ran"].append({"step": "fanout", "result": fanout_updates()})
    elif force == "fanout":
        out["ran"].append({"step": "fanout", "result": fanout_updates()})

    out["state"] = load_state()
    # public-safe summary (no mem content)
    summary = {
        "kind": "daycycle_run_due",
        "generated_at": _now_utc().isoformat(),
        "platform": PLATFORM,
        "steps": [r.get("step") for r in out["ran"]],
        "ok": all((r.get("result") or {}).get("ok", True) for r in out["ran"]),
    }
    docs = ROOT / "docs" / "ops" / "DAYCYCLE_LATEST.summary.json"
    docs.parent.mkdir(parents=True, exist_ok=True)
    docs.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    out["docs_summary"] = str(docs)
    return out


def status() -> Dict[str, Any]:
    st = load_state()
    mp = mem_path()
    lines = 0
    if mp.exists():
        lines = mp.read_text(encoding="utf-8", errors="replace").count("\n")
    return {
        "ok": True,
        "platform": PLATFORM,
        "mem_path": str(mp),
        "mem_lines": lines,
        "state": st,
        "agent_awake": is_agent_awake(),
        "wake_word": ((_cfg().get("agent_protocol") or {}).get("wake_word") or "testtest"),
        "private_repo": (_cfg().get("private_repo") or {}).get("name"),
        "private_path_exists": private_repo_path().exists(),
        "bounds": _cfg().get("bounds"),
    }


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Daycycle mem + consolidation v12.1")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--minute", action="store_true")
    ap.add_argument("--hourly", action="store_true")
    ap.add_argument("--pr", action="store_true")
    ap.add_argument("--daily", action="store_true")
    ap.add_argument("--fanout", action="store_true")
    ap.add_argument("--due", action="store_true", help="run whatever is due")
    ap.add_argument("--all", action="store_true", help="force all steps once")
    ap.add_argument("--wake", action="store_true", help="simulate wake word activation")
    ap.add_argument("--traffic", default="", help="log traffic note for primary instance")
    args = ap.parse_args()

    if args.status:
        print(json.dumps(status(), indent=2, ensure_ascii=False))
        return 0
    if args.wake:
        print(json.dumps(wake_agent("cli"), indent=2, ensure_ascii=False))
        return 0
    if args.traffic:
        print(json.dumps(log_instance_traffic("primary", note=args.traffic), indent=2, ensure_ascii=False))
        return 0
    if args.minute:
        print(json.dumps(minute_tick(), indent=2, ensure_ascii=False))
        return 0
    if args.hourly:
        print(json.dumps(hourly_flush(), indent=2, ensure_ascii=False))
        return 0
    if args.pr:
        print(json.dumps(pr_cycle(), indent=2, ensure_ascii=False))
        return 0
    if args.daily:
        r = daily_top_merge()
        f = fanout_updates()
        print(json.dumps({"merge": r, "fanout": f}, indent=2, ensure_ascii=False))
        return 0 if r.get("ok") else 1
    if args.fanout:
        print(json.dumps(fanout_updates(), indent=2, ensure_ascii=False))
        return 0
    if args.all:
        print(json.dumps(run_due(force="all"), indent=2, ensure_ascii=False)[:8000])
        return 0
    # default due
    print(json.dumps(run_due(), indent=2, ensure_ascii=False)[:8000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
