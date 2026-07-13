import urllib.request
import json
import time

base = "http://127.0.0.1:8000"

def get(path):
    try:
        with urllib.request.urlopen(base + path, timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)[:80]}

print("=== Poll benchmark job ===")
jid = "293c0f24-aeb"
for i in range(6):
    j = get(f"/api/jobs/{jid}")
    print(f"[{i+1}/6] status={j.get('status')}")
    if j.get("status") == "done" or "result" in j:
        print(json.dumps(j, indent=2, ensure_ascii=False)[:1200])
        break
    time.sleep(2)

print("\n=== Full current health snapshot ===")
h = get("/api/health")
snap = {
    "backend": h.get("backend"),
    "mainframe_loaded": h.get("mainframe", {}).get("loaded"),
    "grok_aligned": h.get("v12", {}).get("grok_intern_aligned"),
    "modules": h.get("registry", {}).get("summary", {}).get("loaded"),
    "agents": h.get("registry", {}).get("summary", {}).get("total_agents"),
    "all_ok": h.get("registry", {}).get("summary", {}).get("all_ok"),
    "hyperthreading": h.get("hyperthreading", {}).get("enabled"),
    "cyber_score": h.get("cyber_layer", {}).get("optimization_score"),
}
print(json.dumps(snap, indent=2))

print("\n=== Recommended next actions (heroic) ===")
print("- Run full benchmark or QUBO solve")
print("- POST /api/v12/sync (GoogleMultiAccountSync)")
print("- Advance Layer4 milestone")
print("- Use more agents via /api/agents/*/use")
print("- Open workspace http://127.0.0.1:8080 for GUI ops")
