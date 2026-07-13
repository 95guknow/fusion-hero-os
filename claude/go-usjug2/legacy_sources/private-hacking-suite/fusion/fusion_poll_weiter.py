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

def post(path, data):
    try:
        body = json.dumps(data).encode()
        req = urllib.request.Request(base + path, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)[:120]}

print("=== Poll load_all job 235f1f97-906 ===")
for i in range(4):
    job = get("/api/jobs/235f1f97-906")
    print(f"[{i+1}] {json.dumps(job, indent=2, ensure_ascii=False)[:700]}")
    if job.get("status") not in ["queued", "running"]:
        break
    time.sleep(1.5)

print("\n=== Trigger benchmark via grok/chat ===")
bm = post("/api/grok/chat", {"message": "benchmark", "mode": "full"})
print(json.dumps(bm, indent=2, ensure_ascii=False)[:900])

print("\n=== Quick QUBO via input ===")
q = post("/api/input", {"intent": "qubo", "params": {"size": 8}})
print(json.dumps(q, indent=2, ensure_ascii=False))

print("\n=== Layer 4 status (milestones) ===")
l4 = get("/api/layer4/status")
print("loaded:", l4.get("loaded"))
print("milestones:")
for m in l4.get("milestones", [])[:3]:
    print(f"  - {m.get('id')}: {m.get('title')} [{m.get('status')}]")
