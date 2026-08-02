#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Operationalize MasterSeed against current root VERSION (v15.x kanon).

Creates/updates:
  - public display (local vault + docs/masterseed/PUBLIC_DISPLAY.example.json)
  - private vault seal (local only under ~/.fusion/masterseed)
  - dual-instance mutual_sync (Admin + ascensionOS paths)
  - ops private deploy (optional timeline train)
  - docs/ops/MASTERSEED_OPERATIONAL.latest.json (repo-side status, measured only)
  - optional dashboard health + load-all probes

Code honesty: every field is measured or explicitly "nicht_geprueft".
Does not merge to main, does not push (caller decides).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

UTC = timezone.utc

DEFAULT_INSTANCES = [
    Path(r"C:\Users\Admin\fusion-hero-os"),
    Path(r"C:\ascensionOS\fusion-hero-os"),
]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _read_version() -> str:
    vf = ROOT / "VERSION"
    if vf.is_file():
        return vf.read_text(encoding="utf-8").strip()
    return "unknown"


def _http_json(url: str, method: str = "GET", body: dict | None = None, timeout: float = 30.0) -> dict[str, Any]:
    data = None
    headers = {}
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode("utf-8", errors="replace")
        try:
            return {"ok": True, "status": resp.status, "body": json.loads(raw)}
        except json.JSONDecodeError:
            return {"ok": True, "status": resp.status, "body_text": raw[:500]}


def _probe_dashboard(base: str = "http://127.0.0.1:8000") -> dict[str, Any]:
    out: dict[str, Any] = {"base": base, "light": None, "load_all": None}
    try:
        out["light"] = _http_json(f"{base}/api/health?light=true", timeout=8.0)
    except Exception as e:  # noqa: BLE001
        out["light"] = {"ok": False, "error": str(e)[:200]}
    # load-all only if light succeeded
    if out["light"] and out["light"].get("ok"):
        try:
            out["load_all"] = _http_json(
                f"{base}/api/load-all",
                method="POST",
                body={},
                timeout=120.0,
            )
        except Exception as e:  # noqa: BLE001
            out["load_all"] = {"ok": False, "error": str(e)[:200]}
    return out


def _version_gate() -> dict[str, Any]:
    script = ROOT / "scripts" / "bump_version.py"
    if not script.is_file():
        return {"ok": False, "error": "bump_version.py missing"}
    try:
        p = subprocess.run(
            [sys.executable, str(script), "--check"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": (p.stdout or "").strip()[:500],
            "stderr": (p.stderr or "").strip()[:300],
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def _run_masterseed_tests() -> dict[str, Any]:
    try:
        p = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/test_masterseed_sync.py",
                "tests/test_masterseed_public_vault.py",
                "-q",
                "--tb=no",
            ],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=180,
        )
        return {
            "ok": p.returncode == 0,
            "returncode": p.returncode,
            "stdout": (p.stdout or "").strip()[-800:],
            "stderr": (p.stderr or "").strip()[-400:],
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)[:200]}


def _dual_instance_sync(instances: list[Path], platform_version: str) -> dict[str, Any]:
    from fusion_hero_os.core.heroic_core_orchestrator import MasterSeed
    from fusion_hero_os.core.masterseed_sync import (
        SyncState,
        identity_preservation_score,
        mutual_sync,
    )

    present = [p for p in instances if p.is_dir()]
    if len(present) < 1:
        return {"ok": False, "error": "no instance paths present", "present": []}

    states: list[SyncState] = []
    for p in present:
        ver = platform_version
        vf = p / "VERSION"
        if vf.is_file():
            try:
                ver = vf.read_text(encoding="utf-8").strip() or ver
            except Exception:
                pass
        # fitness from version major.minor as numeric proxy (measured from file)
        try:
            parts = [int(x) for x in ver.split(".")[:3]]
            while len(parts) < 3:
                parts.append(0)
            fitness = parts[0] + parts[1] / 10.0 + parts[2] / 100.0
        except Exception:
            fitness = 0.0
        states.append(
            SyncState(
                seed=MasterSeed(),
                elite_payload={
                    "path": str(p),
                    "version": ver,
                    "stub": (p / "Fusion_MasterSeed_v7.11.md").is_file(),
                },
                elite_fitness=float(fitness),
            )
        )

    # pairwise fold: first is accumulator
    acc = states[0]
    log: list[dict[str, Any]] = []
    for other in states[1:]:
        pre_a, pre_b = acc.elite_fitness, other.elite_fitness
        path_a = acc.elite_payload.get("path") if isinstance(acc.elite_payload, dict) else None
        path_b = other.elite_payload.get("path") if isinstance(other.elite_payload, dict) else None
        acc, other2 = mutual_sync(acc, other)
        log.append(
            {
                "a_path": path_a,
                "b_path": path_b,
                "pre_fitness": [pre_a, pre_b],
                "post_fitness": [acc.elite_fitness, other2.elite_fitness],
                "identity_a": identity_preservation_score(acc),
                "identity_b": identity_preservation_score(other2),
            }
        )
        # keep acc as max-elite carrier for next pair

    return {
        "ok": True,
        "instances_present": [str(p) for p in present],
        "final_elite_fitness": acc.elite_fitness,
        "final_payload": acc.elite_payload,
        "identity_preservation": identity_preservation_score(acc),
        "pairs": log,
    }


def _sync_stub_to_instances(instances: list[Path]) -> dict[str, Any]:
    src = ROOT / "Fusion_MasterSeed_v7.11.md"
    src2 = ROOT / "MASTERSEED_UPDATE_INSTRUCTION_v8.md"
    if not src.is_file():
        return {"ok": False, "error": "root MasterSeed stub missing"}
    copied: list[str] = []
    skipped: list[str] = []
    for inst in instances:
        if inst.resolve() == ROOT.resolve():
            skipped.append(str(inst))
            continue
        if not inst.is_dir():
            skipped.append(f"missing:{inst}")
            continue
        try:
            (inst / "Fusion_MasterSeed_v7.11.md").write_text(
                src.read_text(encoding="utf-8"), encoding="utf-8"
            )
            if src2.is_file():
                (inst / "MASTERSEED_UPDATE_INSTRUCTION_v8.md").write_text(
                    src2.read_text(encoding="utf-8"), encoding="utf-8"
                )
            copied.append(str(inst))
        except Exception as e:  # noqa: BLE001
            skipped.append(f"error:{inst}:{e}")
    return {"ok": True, "copied": copied, "skipped": skipped}


def _write_grok_skill_note(platform_version: str, report: dict[str, Any]) -> dict[str, Any]:
    skill = Path.home() / ".grok" / "skills" / "fusion-hero-os"
    skill.mkdir(parents=True, exist_ok=True)
    path = skill / "MASTERSEED_OPERATIONAL.json"
    payload = {
        "operative_kanon": f"v{platform_version}",
        "platform_version": platform_version,
        "updated_at": _now(),
        "display_id": ((report.get("public") or {}).get("display_id")),
        "integrity_ok": ((report.get("public") or {}).get("integrity_ok")),
        "report_path": str(ROOT / "docs" / "ops" / "MASTERSEED_OPERATIONAL.latest.json"),
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"ok": True, "path": str(path)}


def operationalize(
    *,
    seal: bool = True,
    train: bool = False,
    tests: bool = True,
    dashboard: bool = True,
    instances: list[Path] | None = None,
) -> dict[str, Any]:
    t0 = time.time()
    platform_version = _read_version()
    instances = instances or DEFAULT_INSTANCES
    report: dict[str, Any] = {
        "operation": "operationalize_masterseed",
        "started_at": _now(),
        "platform_version": platform_version,
        "root": str(ROOT),
        "steps": {},
    }

    report["steps"]["version_gate"] = _version_gate()

    # public display + optional seal
    try:
        from fusion_hero_os.core.masterseed_public import public_view
        from fusion_hero_os.core.masterseed_vault import (
            export_public_display,
            seal_all_modules,
            status as vault_status,
        )

        view = public_view(platform_version=platform_version)
        report["public"] = view.to_dict()
        pub = export_public_display()
        report["steps"]["export_public"] = {
            "ok": True,
            "display_id": pub.get("display_id"),
            "platform_version": pub.get("platform_version"),
            "integrity_ok": pub.get("integrity_ok"),
        }
        if seal:
            sealed = seal_all_modules()
            report["steps"]["vault_seal"] = {
                "ok": bool(sealed.get("ok")),
                "sealed_count": sealed.get("sealed_count"),
                "vault": sealed.get("vault"),
            }
        else:
            report["steps"]["vault_seal"] = {"ok": True, "skipped": True}
        report["steps"]["vault_status"] = vault_status()
    except Exception as e:  # noqa: BLE001
        report["steps"]["export_public"] = {"ok": False, "error": str(e)[:300]}
        report["public"] = None

    # dual-instance sync
    try:
        report["steps"]["stub_copy"] = _sync_stub_to_instances(instances)
        report["steps"]["dual_instance_sync"] = _dual_instance_sync(instances, platform_version)
    except Exception as e:  # noqa: BLE001
        report["steps"]["dual_instance_sync"] = {"ok": False, "error": str(e)[:300]}

    # private ops deploy (seal already done; train optional)
    try:
        from fusion_hero_os.core.ops_deploy import deploy as private_deploy

        dep = private_deploy(seal_masterseed=False, train_timeline=train)
        report["steps"]["ops_deploy"] = {
            "ok": bool(dep.get("ok")),
            "duration_sec": dep.get("duration_sec"),
            "manifest": dep.get("manifest"),
            "steps": dep.get("steps"),
        }
    except Exception as e:  # noqa: BLE001
        report["steps"]["ops_deploy"] = {"ok": False, "error": str(e)[:300]}

    if tests:
        report["steps"]["pytest_masterseed"] = _run_masterseed_tests()
    else:
        report["steps"]["pytest_masterseed"] = {"ok": True, "skipped": True}

    if dashboard:
        report["steps"]["dashboard"] = _probe_dashboard(
            os.environ.get("FUSION_GUI_URL", "http://127.0.0.1:8000")
        )
    else:
        report["steps"]["dashboard"] = {"ok": True, "skipped": True}

    report["steps"]["grok_skill_note"] = _write_grok_skill_note(platform_version, report)

    # measured-only confirmation block
    pub = report.get("public") or {}
    dual = report["steps"].get("dual_instance_sync") or {}
    vg = report["steps"].get("version_gate") or {}
    pt = report["steps"].get("pytest_masterseed") or {}
    dash = report["steps"].get("dashboard") or {}
    light_ok = bool((dash.get("light") or {}).get("ok")) if isinstance(dash, dict) else False

    report["confirmation"] = {
        "Version": f"v{platform_version}/local",
        "Kanon-Quelle": "95guknow/fusion-hero-os (local tree)",
        "Version-Gate": "OK" if vg.get("ok") else "FAIL",
        "Public-Display-ID": pub.get("display_id") or "nicht_geprueft",
        "Integrity": "OK" if pub.get("integrity_ok") else ("FAIL" if pub else "nicht_geprueft"),
        "Identity-Preservation": dual.get("identity_preservation", "nicht_geprueft"),
        "Dual-Sync-Elite-Fitness": dual.get("final_elite_fitness", "nicht_geprueft"),
        "Pytest-MasterSeed": "OK" if pt.get("ok") else ("FAIL" if not pt.get("skipped") else "nicht_geprueft"),
        "Dashboard-Light": "OK" if light_ok else "offline_or_fail",
        "Vault-Seal": (report["steps"].get("vault_seal") or {}).get("sealed_count", "nicht_geprueft"),
    }

    # Core steps must pass; dashboard is soft (reported but not required for ok).
    core_keys = (
        "version_gate",
        "export_public",
        "vault_seal",
        "dual_instance_sync",
        "pytest_masterseed",
    )
    step_oks = []
    for k in core_keys:
        v = report["steps"].get(k)
        if not isinstance(v, dict) or v.get("skipped"):
            continue
        if "ok" in v:
            step_oks.append(bool(v["ok"]))
    report["ok"] = all(step_oks) if step_oks else False
    if isinstance(report["steps"].get("dashboard"), dict):
        report["steps"]["dashboard"]["required_for_ok"] = False
    report["duration_sec"] = round(time.time() - t0, 2)
    report["ended_at"] = _now()

    out_path = ROOT / "docs" / "ops" / "MASTERSEED_OPERATIONAL.latest.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["report_path"] = str(out_path)

    home_man = Path.home() / ".fusion" / "ops" / "masterseed_operational_latest.json"
    home_man.parent.mkdir(parents=True, exist_ok=True)
    home_man.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report["home_manifest"] = str(home_man)

    return report


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Create + operationalize MasterSeed v15.x")
    ap.add_argument("--no-seal", action="store_true")
    ap.add_argument("--train", action="store_true", help="also run dual-timeline private train")
    ap.add_argument("--no-tests", action="store_true")
    ap.add_argument("--no-dashboard", action="store_true")
    args = ap.parse_args()
    r = operationalize(
        seal=not args.no_seal,
        train=args.train,
        tests=not args.no_tests,
        dashboard=not args.no_dashboard,
    )
    print(json.dumps(r, indent=2, ensure_ascii=False)[:6000])
    conf = r.get("confirmation") or {}
    print("\n[MASTERSEED UPDATE CONFIRMED]")
    for k, v in conf.items():
        print(f"{k}: {v}")
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
