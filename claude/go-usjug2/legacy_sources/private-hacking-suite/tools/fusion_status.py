import urllib.request
import json

base = "http://127.0.0.1:8000"

def get(path):
    try:
        with urllib.request.urlopen(base + path, timeout=6) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)[:120]}

print("=== /api/health ===")
h = get("/api/health")
keys = ["backend", "fusion_os", "core", "mainframe", "v12", "hyperthreading", "profile", "meta_layer", "cyber_layer"]
for k in keys:
    if k in h:
        print(f"{k}: {json.dumps(h[k], separators=(',',':'))[:300]}")

print("\n=== /api/autoload/status ===")
print(json.dumps(get("/api/autoload/status"), indent=2, ensure_ascii=False)[:1500])

print("\n=== /api/mainframe/pipeline ===")
print(json.dumps(get("/api/mainframe/pipeline"), indent=2, ensure_ascii=False)[:1200])

print("\n=== /api/modules (first 5) ===")
mods = get("/api/modules")
if isinstance(mods, dict) and "modules" in mods:
    print(json.dumps(mods["modules"][:5], indent=2, ensure_ascii=False))
else:
    print(json.dumps(mods, indent=2, ensure_ascii=False)[:800])

print("\n=== /api/agents ===")
print(json.dumps(get("/api/agents"), indent=2, ensure_ascii=False)[:1000])

print("\n=== /api/grok/status ===")
print(json.dumps(get("/api/grok/status"), indent=2, ensure_ascii=False)[:800])
