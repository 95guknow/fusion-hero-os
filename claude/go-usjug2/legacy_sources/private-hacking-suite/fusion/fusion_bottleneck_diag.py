import urllib.request
import json

base = "http://127.0.0.1:8000"

def get(path):
    try:
        with urllib.request.urlopen(base + path, timeout=6) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)[:100]}

print("=== 1. Full Health ===")
h = get("/api/health")
print(json.dumps({
    "backend": h.get("backend"),
    "mainframe": h.get("mainframe"),
    "v12": h.get("v12"),
    "hyperthreading": h.get("hyperthreading"),
    "profile": h.get("profile"),
    "meta_layer": h.get("meta_layer"),
    "cyber_layer": h.get("cyber_layer", {}),
    "registry_summary": h.get("registry", {}).get("summary"),
}, indent=2, ensure_ascii=False))

print("\n=== 2. Resources Plan ===")
print(json.dumps(get("/api/resources/plan"), indent=2, ensure_ascii=False))

print("\n=== 3. Signal Health (full) ===")
print(json.dumps(get("/api/signal/health?layer=full"), indent=2, ensure_ascii=False)[:2000])

print("\n=== 4. Hyperthreading Status ===")
print(json.dumps(get("/api/hyperthreading"), indent=2, ensure_ascii=False))

print("\n=== 5. Profile Status ===")
print(json.dumps(get("/api/profile/status"), indent=2, ensure_ascii=False))

print("\n=== 6. Windows Substrate Tune (current) ===")
print(json.dumps(get("/api/windows/substrate/tune"), indent=2, ensure_ascii=False))
