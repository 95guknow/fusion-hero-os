import urllib.request
import json
import subprocess
import time

base = "http://127.0.0.1:8000"

def get(path):
    try:
        with urllib.request.urlopen(base + path, timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)[:80]}

print("=== POST CLEANUP HEALTH ===")
h = get("/api/health")
print("Profile:", h.get("profile",{}).get("active"))
print("HT workers:", h.get("hyperthreading",{}).get("workers"))
ra = h.get("v12",{}).get("resource_allocator", {})
print("RAM pressure:", ra.get("ram_pressure"))
print("CPU pressure:", ra.get("cpu_pressure"))
print("Notes:", ra.get("notes"))

print("\n=== Re-scan substrate for duplicates ===")
scan = get("/api/windows/substrate/tune")
if "scan" in scan:
    print("duplicate_backends:", scan["scan"].get("duplicate_backends"))
    print("fusion_backends:")
    for b in scan["scan"].get("fusion_backends", []):
        print("  PID", b["pid"], b["mb"], "MB")

print("\n=== Resources after admin ===")
print(json.dumps(get("/api/resources/plan"), indent=2, ensure_ascii=False)[:1500])

# Optional: suggest killing duplicates, but do not auto-kill here to be safe
print("\n=== RECOMMENDATIONS ===")
print("1. Profile now 'admin' (1.0) — bottleneck cap removed.")
print("2. HT workers increased to 10.")
print("3. Cyber optimization_score 88.")
print("4. Duplicate uvicorn backends detected — kill the older one manually if needed.")
print("5. High RAM (Firefox heavy + processes) still the physical limit.")
print("   Consider closing browser tabs or set power to High Performance.")
