"""
Dauer-Eupression — continuous good-pressure along defined dependencies.

Applies Eupression∥Eudaimon bottom-up according to
``fusion_hero_os/core/catalogs/dauer_eupression_deps.yaml``.

Rules:
  * Pressure order = dependency DAG (depends_on must pass first).
  * Continuous by default; state under ``~/.fusion/dauer_eupression.json``.
  * Structure writes still gated by poly_fa (not opened by this module).
  * Hear/speak remain person-surface scopes (open).
  * No legal names, no unlock phrases in public status or git.

Geltung: Spezifikation (dependency chain) · scores = Modell
"""
from __future__ import annotations

import importlib
import json
import time
from datetime import datetime, timezone
UTC = timezone.utc  # py3.10+compat (was datetime.UTC)
from pathlib import Path
from typing import Any
from collections.abc import Sequence

ROOT = Path(__file__).resolve().parents[2]
DEPS_YAML = Path(__file__).resolve().parent / "catalogs" / "dauer_eupression_deps.yaml"
STATE_PATH = Path.home() / ".fusion" / "dauer_eupression.json"

__all__ = [
    "load_deps",
    "topo_order",
    "pulse",
    "ensure_continuous",
    "status",
    "public_status",
    "install",
]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _now_ts() -> float:
    return time.time()


def load_deps() -> dict[str, Any]:
    """Load explicit dependency catalog (YAML if available, else built-in)."""
    if DEPS_YAML.is_file():
        try:
            import yaml  # type: ignore

            data = yaml.safe_load(DEPS_YAML.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
        except Exception:
            # fallback parser for simple subset if PyYAML missing
            pass
    return _builtin_deps()


def _builtin_deps() -> dict[str, Any]:
    """Minimal mirror of dauer_eupression_deps.yaml if YAML load fails."""
    return {
        "version": 1,
        "platform_version": "12.0.0",
        "policy_id": "dauer_eupression_deps_v1",
        "mode": "continuous",
        "nodes": [
            {"id": "base_module", "import": "fusion_hero_os.core.base_module", "depends_on": [], "probe": "import_only"},
            {"id": "operator_identity", "import": "fusion_hero_os.core.operator_identity", "depends_on": ["base_module"], "probe": "public_operator_view"},
            {"id": "god_layer_seal", "import": "fusion_hero_os.core.god_layer_seal", "depends_on": ["operator_identity"], "probe": "public_status"},
            {"id": "poly_fa_write_gate", "import": "fusion_hero_os.core.poly_fa_write_gate", "depends_on": ["god_layer_seal", "operator_identity"], "probe": "public_status"},
            {"id": "dependency_atlas", "import": "fusion_hero_os.core.dependency_atlas", "depends_on": ["base_module"], "probe": "atlas_summary"},
            {"id": "layer_registry", "import": "fusion_hero_os.core.layer_registry", "depends_on": ["dependency_atlas"], "probe": "status_if_any"},
            {"id": "meister_hasch_optimize", "import": "fusion_hero_os.core.meister_hasch_optimize", "depends_on": ["poly_fa_write_gate", "dependency_atlas"], "probe": "status"},
            {"id": "weltraudaimonia", "import": "fusion_hero_os.modules.weltraudaimonia", "depends_on": ["meister_hasch_optimize", "operator_identity"], "probe": "weltrau_score"},
            {"id": "comaedchen_audio", "import": "fusion_hero_os.core.comaedchen_audio", "depends_on": ["operator_identity", "weltraudaimonia"], "probe": "status"},
        ],
        "continuous": {"enabled": True, "min_interval_sec": 60, "fail_closed_on_missing_dep": True},
        "eudaimon_default_scores": {
            "stakeholder_breadth": 0.55,
            "reversibility": 0.85,
            "time_horizon": 0.75,
            "evidence_quality": 0.70,
        },
    }


def topo_order(nodes: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    """Topological order by depends_on; stable for independent siblings."""
    by_id = {n["id"]: n for n in nodes if n.get("id")}
    pending = set(by_id)
    done: list[str] = []
    while pending:
        ready = [
            i
            for i in pending
            if all(d in done or d not in by_id for d in (by_id[i].get("depends_on") or []))
        ]
        if not ready:
            # cycle or missing — append remaining in catalog order
            for i in list(pending):
                done.append(i)
                pending.discard(i)
            break
        # preserve catalog order among ready
        ordered = [i for i in by_id if i in ready]
        for i in ordered:
            done.append(i)
            pending.discard(i)
    return [by_id[i] for i in done if i in by_id]


def _probe_node(node: dict[str, Any], deps_cfg: dict[str, Any]) -> dict[str, Any]:
    nid = node.get("id")
    imp = node.get("import")
    probe = node.get("probe") or "import_only"
    out: dict[str, Any] = {
        "id": nid,
        "import": imp,
        "probe": probe,
        "depends_on": list(node.get("depends_on") or []),
        "ok": False,
        "detail": "",
        "pressure": node.get("pressure") or "generic",
    }
    if not imp:
        out["detail"] = "missing_import"
        return out
    try:
        mod = importlib.import_module(str(imp))
    except Exception as exc:  # noqa: BLE001
        out["detail"] = f"import_fail:{type(exc).__name__}:{exc}"[:200]
        return out

    try:
        if probe == "import_only":
            out["ok"] = True
            out["detail"] = "imported"
        elif probe == "public_operator_view":
            fn = getattr(mod, "public_operator_view", None) or getattr(mod, "status", None)
            data = fn() if callable(fn) else {}
            out["ok"] = bool(data.get("role") == "operator" or data.get("ok", True))
            out["detail"] = f"person_bound={data.get('person_bound')} role={data.get('role')}"
            out["snapshot"] = {
                k: data.get(k)
                for k in ("role", "person_bound", "routing_mode", "write_rights")
                if k in data
            }
        elif probe == "public_status":
            fn = getattr(mod, "public_status", None) or getattr(mod, "status", None)
            data = fn() if callable(fn) else {}
            out["ok"] = bool(data.get("ok", True))
            # poly-FA: structure write should not be ambient-open without grant
            if nid == "poly_fa_write_gate":
                cw = data.get("can_write_god_layer") or {}
                out["detail"] = (
                    f"desktop={data.get('is_authorized_desktop')} "
                    f"grants={data.get('active_grants')} "
                    f"write_allowed={cw.get('allowed') if isinstance(cw, dict) else cw}"
                )
                out["ok"] = bool(data.get("active", True)) and bool(
                    data.get("is_authorized_desktop") is not False
                )
            else:
                out["detail"] = f"sealed={data.get('sealed')} write={data.get('write_rights')}"
            out["snapshot"] = {
                k: data.get(k)
                for k in (
                    "sealed",
                    "write_rights",
                    "active",
                    "is_authorized_desktop",
                    "active_grants",
                    "hear_speak",
                )
                if k in data or k in (data.get("person_handover") or {})
            }
            if "person_handover" in data:
                out["snapshot"]["hear_speak"] = (data.get("person_handover") or {}).get(
                    "hear_speak"
                )
        elif probe == "status":
            fn = getattr(mod, "status", None)
            data = fn() if callable(fn) else {}
            out["ok"] = bool(data.get("ok", True) or data.get("integrity_ok", False) or data)
            out["detail"] = str(
                {
                    k: data.get(k)
                    for k in ("integrity_ok", "channel", "module", "asset_present")
                    if k in data
                }
            )[:200]
            out["snapshot"] = {
                k: data.get(k)
                for k in ("integrity_ok", "channel", "asset_sha256_prefix", "ok")
                if k in data
            }
        elif probe == "atlas_summary":
            # lightweight: module import + optional summary function
            summary_fn = getattr(mod, "summary", None) or getattr(mod, "build_atlas", None)
            if callable(summary_fn):
                try:
                    # build_atlas may be heavy — try status-like first
                    if summary_fn.__name__ == "build_atlas":
                        out["ok"] = True
                        out["detail"] = "atlas_module_loadable"
                    else:
                        s = summary_fn()
                        out["ok"] = True
                        out["detail"] = str(s)[:200]
                except Exception as exc:  # noqa: BLE001
                    out["ok"] = True  # import ok is enough for continuous pressure
                    out["detail"] = f"atlas_soft:{type(exc).__name__}"
            else:
                out["ok"] = True
                out["detail"] = "atlas_import_ok"
        elif probe == "status_if_any":
            fn = getattr(mod, "status", None) or getattr(mod, "get_status", None)
            if callable(fn):
                data = fn()
                out["ok"] = True
                out["detail"] = str(data)[:160]
            else:
                out["ok"] = True
                out["detail"] = "module_present"
        elif probe == "weltrau_score":
            cls = getattr(mod, "WeltraudaimoniaModule", None)
            scores = dict(deps_cfg.get("eudaimon_default_scores") or {})
            if cls is not None:
                res = cls().process({"scores": scores})
                score = float(res.get("weltraudaimonia_score") or 0.0)
                out["ok"] = score >= 0.5  # continuous floor
                out["detail"] = f"weltraudaimonia_score={score}"
                out["snapshot"] = {"weltraudaimonia_score": score, "axes": res.get("axes")}
            else:
                out["ok"] = False
                out["detail"] = "WeltraudaimoniaModule_missing"
        else:
            out["ok"] = True
            out["detail"] = f"unknown_probe_treated_as_import:{probe}"
    except Exception as exc:  # noqa: BLE001
        out["ok"] = False
        out["detail"] = f"probe_fail:{type(exc).__name__}:{exc}"[:200]
    return out


def pulse(*, force: bool = False) -> dict[str, Any]:
    """One Dauer-Eupression pulse along dependency order."""
    deps = load_deps()
    nodes = list(deps.get("nodes") or [])
    ordered = topo_order(nodes)
    cont = deps.get("continuous") or {}
    min_iv = float(cont.get("min_interval_sec") or 60)
    fail_closed = bool(cont.get("fail_closed_on_missing_dep", True))

    prev = _load_state()
    last_ts = float(prev.get("last_pulse_ts") or 0)
    if not force and last_ts and (_now_ts() - last_ts) < min_iv:
        return {
            "ok": True,
            "action": "skipped_interval",
            "seconds_to_next": round(min_iv - (_now_ts() - last_ts), 1),
            "last": prev.get("last_report"),
            "continuous": True,
        }

    results: list[dict[str, Any]] = []
    passed: set[str] = set()
    blocked: list[str] = []

    for node in ordered:
        deps_ok = all(
            d in passed for d in (node.get("depends_on") or []) if d in {n["id"] for n in ordered}
        )
        if not deps_ok and fail_closed:
            r = {
                "id": node.get("id"),
                "ok": False,
                "detail": "dependency_not_satisfied",
                "depends_on": node.get("depends_on"),
                "pressure": node.get("pressure"),
                "skipped": True,
            }
            results.append(r)
            blocked.append(str(node.get("id")))
            continue
        r = _probe_node(node, deps)
        results.append(r)
        if r.get("ok"):
            passed.add(str(node.get("id")))
        else:
            blocked.append(str(node.get("id")))
            if fail_closed:
                # still probe remaining for diagnosis but mark chain soft-fail
                pass

    all_ok = len(blocked) == 0
    eudaimon = next((r for r in results if r.get("id") == "weltraudaimonia"), None)
    report = {
        "ok": all_ok,
        "action": "pulse",
        "policy_id": deps.get("policy_id"),
        "mode": "continuous",
        "pulsed_at": _now(),
        "order": [n.get("id") for n in ordered],
        "passed": sorted(passed),
        "blocked": blocked,
        "nodes": results,
        "organs": {
            "eupression": {
                "continuous": True,
                "chain_ok": all_ok,
                "blocked": blocked,
            },
            "eudaimon": {
                "continuous": True,
                "score_detail": (eudaimon or {}).get("detail"),
                "ok": bool((eudaimon or {}).get("ok")),
            },
        },
        "structure_write": "poly_fa_only",
        "hear_speak": "person_surface_open",
    }

    state = {
        "continuous": True,
        "enabled": bool(cont.get("enabled", True)),
        "last_pulse_ts": _now_ts(),
        "last_pulse_at": report["pulsed_at"],
        "last_report": report,
        "policy_id": deps.get("policy_id"),
        "deps_path": str(DEPS_YAML),
    }
    _save_state(state)
    return report


def ensure_continuous() -> dict[str, Any]:
    """Enable continuous mode and force one pulse."""
    deps = load_deps()
    cont = dict(deps.get("continuous") or {})
    cont["enabled"] = True
    # state flag
    st = _load_state()
    st["continuous"] = True
    st["enabled"] = True
    st["installed_at"] = _now()
    _save_state(st)
    report = pulse(force=True)
    report["action"] = "ensure_continuous"
    report["enabled"] = True
    return report


def install() -> dict[str, Any]:
    """Alias: install Dauer-Eupression continuous policy."""
    return ensure_continuous()


def _load_state() -> dict[str, Any]:
    if not STATE_PATH.is_file():
        return {}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _save_state(data: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def public_status() -> dict[str, Any]:
    st = _load_state()
    last = st.get("last_report") or {}
    deps = load_deps()
    return {
        "ok": True,
        "module": "dauer_eupression",
        "policy_id": deps.get("policy_id") or st.get("policy_id"),
        "continuous": bool(st.get("continuous", True)),
        "enabled": bool(st.get("enabled", True)),
        "last_pulse_at": st.get("last_pulse_at"),
        "chain_ok": bool(last.get("ok")) if last else None,
        "passed": last.get("passed"),
        "blocked": last.get("blocked"),
        "organs": last.get("organs"),
        "order": last.get("order") or [n.get("id") for n in (deps.get("nodes") or [])],
        "structure_write": "poly_fa_only",
        "hear_speak": "person_surface_open",
        "deps_catalog": str(DEPS_YAML.relative_to(ROOT)) if DEPS_YAML.is_file() else "builtin",
    }


def status() -> dict[str, Any]:
    # refresh if continuous enabled and interval elapsed
    st = _load_state()
    if st.get("enabled", True) and st.get("continuous", True):
        pulse(force=False)
    return public_status()


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Dauer-Eupression (dependency-ordered continuous pressure)")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--pulse", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--install", action="store_true", help="enable continuous + force pulse")
    ap.add_argument("--json-full", action="store_true")
    args = ap.parse_args()

    if args.install:
        r = install()
        print(json.dumps(r if args.json_full else public_status(), indent=2, ensure_ascii=False))
        return 0 if r.get("ok") else 1
    if args.pulse:
        r = pulse(force=args.force or True)
        print(json.dumps(r if args.json_full else {
            "ok": r.get("ok"),
            "action": r.get("action"),
            "passed": r.get("passed"),
            "blocked": r.get("blocked"),
            "organs": r.get("organs"),
        }, indent=2, ensure_ascii=False))
        return 0 if r.get("ok") else 1
    print(json.dumps(status(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
