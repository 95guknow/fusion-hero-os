"""Subagent Llama-Tests — parallel, ressourcenbewusst."""
import os
import sys

os.environ.setdefault("FUSION_LLAMA_SUBAGENT_SKIP_GENERATE", "1")

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_CORE = os.path.join(_ROOT, "core")
if _CORE not in sys.path:
    sys.path.insert(0, _CORE)

from llama_subagent_tester import run, status, all_subagents


def test_status_reports_available_subagents():
    st = status()
    assert st["available_subagents"], "es sollten Subagenten registriert sein"


def test_llama_subagent_tracks():
    result = run(subagents=list(all_subagents().keys()))
    assert result["subagents_ok"] >= 4, "mindestens Status/CLI/Bridge-Tests müssen OK sein"


def main():
    test_status_reports_available_subagents()
    st = status()
    print("subagents available:", st["available_subagents"])
    print("generate skip:", st["generate_would_skip"])
    print("resource:", st.get("resource_recommendation", {}).get("mode"))

    result = run(subagents=list(all_subagents().keys()))
    assert result["subagents_ok"] >= 4
    print("status:", result["status"])
    print("ok:", result["subagents_ok"], "/", result["subagents_total"])
    for track in result["tracks"]:
        name = track.get("subagent")
        ok = track.get("ok")
        err = track.get("error")
        res = track.get("result") or {}
        skip = res.get("skipped")
        print(f"  {name}: {'SKIP' if skip else ('OK' if ok else 'FAIL')} {err or ''}")
    print("ALL LLAMA SUBAGENT TESTS PASSED")


if __name__ == "__main__":
    main()
