import urllib.request
import json
import time

base = "http://127.0.0.1:8000"

def get(path):
    try:
        with urllib.request.urlopen(base + path, timeout=6) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)[:80]}

def post(path, data):
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(base + path, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)[:120]}

print("=== BOTTLENECK DIAGNOSIS SUMMARY ===")
print("Current profile: two_thirds (capped 2/3)")
print("RAM pressure: ~85-87% (critical)")
print("Workers capped at 6 / usable ~1-4 due to profile")
print("HT enabled but throttled by profile")

print("\n=== 1. SWITCH TO ADMIN PROFILE (full power) ===")
prof = post("/api/profile/set", {"name": "admin"})
print(json.dumps(prof, indent=2, ensure_ascii=False))

print("\n=== 2. SET PERFORMANCE RATIO 1.0 ===")
perf = post("/api/performance/set", {"ratio": 1.0})
print(json.dumps(perf, indent=2, ensure_ascii=False))

print("\n=== 3. ENABLE FULL HYPERTHREADING (max workers) ===")
ht = post("/api/hyperthreading", {"enabled": True})
print(json.dumps(ht, indent=2, ensure_ascii=False))

print("\n=== 4. Re-run resources plan ===")
print(json.dumps(get("/api/resources/plan"), indent=2, ensure_ascii=False))

print("\n=== 5. Trigger substrate tune (POST) ===")
tune = post("/api/windows/substrate/tune", {})
print(json.dumps(tune, indent=2, ensure_ascii=False))

print("\n=== 6. Cyber layer activate / RAM watch ===")
cyber = post("/api/windows/cyber-layer/activate", {})
print(json.dumps(cyber, indent=2, ensure_ascii=False))

print("\n=== 7. Re-trigger full autoload for re-allocation ===")
al = post("/api/autoload/run", {"phase": "full", "force": True, "sync": False, "attach_meta": True})
print("Autoload accepted:", al.get("accepted") or "running")

time.sleep(3)

print("\n=== FINAL SNAPSHOT ===")
h = get("/api/health")
snap = {
    "profile": h.get("profile", {}).get("active"),
    "performance_ratio": h.get("hyperthreading", {}).get("performance_ratio"),
    "workers": h.get("hyperthreading", {}).get("workers"),
    "ram_pressure": h.get("v12", {}).get("resource_allocator", {}).get("ram_pressure"),
    "cpu_pressure": h.get("v12", {}).get("resource_allocator", {}).get("cpu_pressure"),
    "notes": h.get("v12", {}).get("resource_allocator", {}).get("notes"),
    "all_ok": h.get("registry_summary", {}).get("all_ok"),
}
print(json.dumps(snap, indent=2, ensure_ascii=False))

print("\n=== Bottleneck fix applied. Check workspace or run more if needed. ===")
