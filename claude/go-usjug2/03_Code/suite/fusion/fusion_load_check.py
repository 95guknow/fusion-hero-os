import urllib.request
import json
import time

base = "http://127.0.0.1:8000"

def get(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def post(url, data):
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

print("=== Current Health ===")
h = get(base + "/api/health?light=true")
print(json.dumps(h, indent=2)[:1500])

print("\n=== Triggering /api/autoload/run (full) ===")
al = post(base + "/api/autoload/run", {"phase": "full", "force": True, "sync": True, "attach_meta": True})
print(json.dumps(al, indent=2)[:2000])

print("\n=== Waiting for mainframe loaded (up to 60s) ===")
for i in range(60):
    mf = get(base + "/api/mainframe/status")
    if mf.get("loaded"):
        print("Mainframe loaded:", mf.get("version"))
        break
    time.sleep(1)
else:
    print("Mainframe still not loaded:", mf)

print("\n=== Final Health ===")
h2 = get(base + "/api/health")
print("backend:", h2.get("backend"))
print("mainframe loaded:", h2.get("mainframe", {}).get("loaded"))
print("grok aligned:", h2.get("v12", {}).get("grok_intern_aligned"))
print("modules loaded:", h2.get("registry", {}).get("summary", {}).get("loaded"))
