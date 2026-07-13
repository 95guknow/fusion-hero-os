import urllib.request
import json

base = "http://127.0.0.1:8000"

def post(path, data):
    try:
        req = urllib.request.Request(base + path, data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)[:100]}

print("=== POST /api/v12/sync (GoogleMultiAccountSync) ===")
sync = post("/api/v12/sync", {"mode": "delta"})
print(json.dumps(sync, indent=2, ensure_ascii=False)[:1000])

print("\n=== POST /api/input with benchmark intent ===")
inp = post("/api/input", {"intent": "benchmark", "params": {"type": "qubo", "parallel": True}})
print(json.dumps(inp, indent=2, ensure_ascii=False))

print("\n=== Final health check ===")
h = json.loads(urllib.request.urlopen(base + "/api/health", timeout=5).read().decode())
print("Mainframe:", h.get("mainframe", {}).get("loaded"))
print("Modules loaded:", h.get("registry", {}).get("summary", {}).get("loaded"))
print("All OK:", h.get("registry", {}).get("summary", {}).get("all_ok"))
