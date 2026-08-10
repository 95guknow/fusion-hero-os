#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CoEV Proberunde: 10 Generationen, Zeitbudget 5 Minuten, Ergebnisbericht.

  python scripts/coev_probe_10g.py
  python scripts/coev_probe_10g.py --gens 10 --budget 300
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    ap = argparse.ArgumentParser(description="CoEV probe 10g / 5min")
    ap.add_argument("--gens", type=int, default=10)
    ap.add_argument("--budget", type=float, default=300.0, help="seconds")
    args = ap.parse_args()

    gens = args.gens
    budget_s = args.budget
    t0 = time.perf_counter()
    out_dir = Path.home() / ".fusion" / "coevolution"
    out_dir.mkdir(parents=True, exist_ok=True)

    report: dict = {
        "run_type": "COEV_PROBE_10G",
        "label": f"Proberunde CoEV {gens}g / {int(budget_s // 60)}min",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "budget_s": budget_s,
        "target_generations": gens,
        "platform_hint": "Fusion Hero OS v13.0.0 + Ascension v9.10 aspirational",
        "tracks": {},
        "errors": [],
        "verdict": {},
    }

    def remaining() -> float:
        return budget_s - (time.perf_counter() - t0)

    def elapsed() -> float:
        return round(time.perf_counter() - t0, 3)

    # --- Track A: Pure-Core Coevolution ---
    track_a: dict = {"name": "pure_core_coevolution", "status": "pending"}
    try:
        from fusion_hero_os.core.pure_core_coevolution import (
            assert_core_not_replaced,
            mutual_cycle,
            status as pc_status,
        )

        t_a = time.perf_counter()
        st_before = pc_status()
        out = mutual_cycle(gens)
        t_a_dt = time.perf_counter() - t_a
        rej_ok, rej_msg = assert_core_not_replaced("llm")
        acc_ok, acc_msg = assert_core_not_replaced("pure_core")
        final = out.get("final") or {}
        track_a = {
            "name": "pure_core_coevolution",
            "status": "ok" if out.get("ok") else "degraded",
            "duration_s": round(t_a_dt, 3),
            "ok": out.get("ok"),
            "trajectory": out.get("trajectory"),
            "mutual_score": final.get("mutual_score"),
            "integrity_ok": final.get("integrity_ok"),
            "core_ids": final.get("core_ids"),
            "foreign_ids": final.get("foreign_ids"),
            "crosspoll_sources": final.get("crosspoll_sources"),
            "status_before": {
                "core_count": st_before.get("core_count"),
                "foreign_count": st_before.get("foreign_count"),
                "mutual_score": st_before.get("mutual_score"),
                "integrity_ok": st_before.get("integrity_ok"),
            },
            "reject_llm_as_sot": {"accepted": rej_ok, "message": rej_msg},
            "accept_pure_core_sot": {"accepted": acc_ok, "message": acc_msg},
        }
    except Exception as e:
        track_a = {
            "name": "pure_core_coevolution",
            "status": "error",
            "error": str(e),
            "trace": traceback.format_exc()[-800:],
        }
        report["errors"].append(f"TrackA: {e}")
    report["tracks"]["A_pure_core"] = track_a

    # --- Track B: AscensionCore + CEC ---
    if remaining() > 10:
        try:
            from ascension_os.core.ascension_core import get_ascension_core
            from ascension_os.core.coevolutionary_closure import get_coevolutionary_closure

            t_b = time.perf_counter()
            core = get_ascension_core()
            cec = get_coevolutionary_closure()
            for name, mode in (
                ("heroic", "heroic"),
                ("ascension", "ascension"),
                ("coevolution_probe", "experimental"),
            ):
                cec.create_track(name, mode=mode)
            cec.register_component("ascension_core", core, track="ascension")
            cec.register_component("probe_runner", {"gens": gens}, track="coevolution_probe")
            gen_out = core.run_generation(generations=gens)
            status = core.get_status() if hasattr(core, "get_status") else {}
            cec_status = cec.get_status()
            t_b_dt = time.perf_counter() - t_b
            gens_detail = []
            if core.evolution_engine and core.evolution_engine.generations:
                for g in core.evolution_engine.generations[-gens:]:
                    gens_detail.append(
                        {
                            "n": g.number,
                            "fitness": round(g.fitness_score, 2),
                            "improvements": g.improvements[:3],
                            "ts": g.timestamp,
                        }
                    )
            track_b = {
                "name": "ascension_cec_10g",
                "status": "ok"
                if isinstance(gen_out, dict) and gen_out.get("generations_run") == gens
                else "partial",
                "duration_s": round(t_b_dt, 3),
                "ascension_version": getattr(core, "version", None),
                "generation_result": gen_out,
                "generations_detail": gens_detail,
                "cec_status": cec_status,
                "core_status_keys": list(status.keys()) if isinstance(status, dict) else [],
                "modules_loaded": {
                    "evolution_engine": core.evolution_engine is not None,
                    "cec": core.cec is not None,
                    "persistent_sisyphos": getattr(core, "persistent_sisyphos", None) is not None,
                    "stage9_tracker": getattr(core, "stage9_tracker", None) is not None,
                },
            }
            if getattr(core, "stage9_tracker", None) and hasattr(core, "get_stage9_status"):
                try:
                    track_b["stage9"] = core.get_stage9_status()
                except Exception as se:
                    track_b["stage9_error"] = str(se)
        except Exception as e:
            track_b = {
                "name": "ascension_cec_10g",
                "status": "error",
                "error": str(e),
                "trace": traceback.format_exc()[-800:],
            }
            report["errors"].append(f"TrackB: {e}")
    else:
        track_b = {"name": "ascension_cec_10g", "status": "skipped", "reason": "budget_exhausted"}
    report["tracks"]["B_ascension_cec"] = track_b

    # --- Track C: GenerationalEvolutionEngine standalone ---
    if remaining() > 5:
        try:
            from ascension_os.evolution.generational_engine import GenerationalEvolutionEngine

            t_c = time.perf_counter()
            eng = GenerationalEvolutionEngine()
            state = {
                "is_sustainable": False,
                "satisfaction": 0.42,
                "load": 0.78,
                "fail_closed_active": False,
                "masterseed_integrity": True,
                "ascension_mode_active": False,
            }
            gens_list = eng.run_generations(state, generations=gens)
            summary = eng.get_evolution_summary()
            track_c = {
                "name": "gen_engine_standalone",
                "status": "ok",
                "duration_s": round(time.perf_counter() - t_c, 3),
                "summary": summary,
                "fitness_curve": [round(g.fitness_score, 2) for g in gens_list],
                "start_fitness": round(gens_list[0].fitness_score, 2) if gens_list else None,
                "end_fitness": round(gens_list[-1].fitness_score, 2) if gens_list else None,
                "delta_fitness": round(gens_list[-1].fitness_score - gens_list[0].fitness_score, 2)
                if gens_list
                else None,
            }
        except Exception as e:
            track_c = {"name": "gen_engine_standalone", "status": "error", "error": str(e)}
            report["errors"].append(f"TrackC: {e}")
    else:
        track_c = {"name": "gen_engine_standalone", "status": "skipped", "reason": "budget_exhausted"}
    report["tracks"]["C_gen_engine"] = track_c

    # --- Track D: highest layer optional ---
    if remaining() > 15:
        try:
            sys.path.insert(0, str(ROOT / "03_Code" / "heroic-highest-layer"))
            from highest_layer import HighestLayer  # type: ignore

            t_d = time.perf_counter()
            hl = HighestLayer()
            results = hl.run_generation_cycle(gens)
            if results and isinstance(results[0], dict):
                fitnesses = [r.get("fitness", r.get("score")) for r in results]
            else:
                fitnesses = [getattr(r, "fitness", None) for r in (results or [])]
            track_d = {
                "name": "highest_layer_10g",
                "status": "ok",
                "duration_s": round(time.perf_counter() - t_d, 3),
                "n": len(results) if results else 0,
                "fitness_sample": fitnesses[:10] if fitnesses else [],
            }
        except Exception as e:
            track_d = {
                "name": "highest_layer_10g",
                "status": "error_or_unavailable",
                "error": str(e)[:300],
            }
    else:
        track_d = {"name": "highest_layer_10g", "status": "skipped", "reason": "budget_or_priority"}
    report["tracks"]["D_highest_layer"] = track_d

    total = elapsed()
    ok_tracks = sum(1 for t in report["tracks"].values() if t.get("status") == "ok")
    err_tracks = sum(1 for t in report["tracks"].values() if t.get("status") == "error")
    mutual = report["tracks"].get("A_pure_core", {}).get("mutual_score")
    fit_end = report["tracks"].get("C_gen_engine", {}).get("end_fitness")
    fit_delta = report["tracks"].get("C_gen_engine", {}).get("delta_fitness")
    integrity = report["tracks"].get("A_pure_core", {}).get("integrity_ok")
    gen_res = report["tracks"].get("B_ascension_cec", {}).get("generation_result") or {}
    gens_run_b = gen_res.get("generations_run")

    passed = (
        ok_tracks >= 2
        and err_tracks == 0
        and integrity is not False
        and (
            gens_run_b == gens
            or report["tracks"]["B_ascension_cec"].get("status") == "ok"
        )
        and total <= budget_s
    )
    if ok_tracks >= 2 and total <= budget_s and not passed:
        overall = "PASS_WITH_NOTES"
    elif passed:
        overall = "PASS"
    else:
        overall = "FAIL"

    notes = []
    if mutual is not None and mutual < 0.3:
        notes.append("mutual_score niedrig — Katalog/Evidence-Pfade prüfen")
    rej = report["tracks"]["A_pure_core"].get("reject_llm_as_sot") or {}
    if rej.get("accepted") is True:
        notes.append("WARN: LLM als Source-of-Truth wurde akzeptiert (sollte rejected sein)")
    elif rej.get("accepted") is False:
        notes.append("OK: LLM als SoT abgelehnt (Pure-Core-Policy)")
    if fit_delta is not None and fit_delta > 0:
        notes.append(f"Fitness-Trend positiv (+{fit_delta}) über {gens}g")

    report["finished_at"] = datetime.now(timezone.utc).isoformat()
    report["elapsed_s"] = total
    report["budget_used_pct"] = round(100.0 * total / budget_s, 2)
    report["verdict"] = {
        "overall": overall,
        "ok_tracks": ok_tracks,
        "error_tracks": err_tracks,
        "within_budget": total <= budget_s,
        "generations_target": gens,
        "mutual_score": mutual,
        "gen_engine_end_fitness": fit_end,
        "gen_engine_delta": fit_delta,
        "integrity_ok": integrity,
        "notes": notes,
    }

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"coev_probe_10g_{stamp}.json"
    latest = out_dir / "coev_probe_10g_latest.json"
    payload = json.dumps(report, indent=2, ensure_ascii=False)
    out_path.write_text(payload, encoding="utf-8")
    latest.write_text(payload, encoding="utf-8")

    print(payload)
    print(f"\n=== REPORT_SAVED: {out_path} ===")
    print(f"=== LATEST: {latest} ===")
    verdict = report["verdict"]["overall"]
    print(f"=== VERDICT: {verdict} | elapsed={total}s / {budget_s}s ===")
    return 0 if overall in ("PASS", "PASS_WITH_NOTES") else 1


if __name__ == "__main__":
    raise SystemExit(main())
