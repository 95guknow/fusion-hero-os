import urllib.request
import json
import time

base = "http://127.0.0.1:8000"

def get(path, timeout=6):
    try:
        with urllib.request.urlopen(base + path, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)[:100]}

def post(path, data, timeout=30):
    try:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(base + path, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)[:150]}

print("=== Current Layer4 / Highest Layer ===")
print(json.dumps(get("/api/layer4/status"), indent=2, ensure_ascii=False)[:1200])

print("\n=== Trying /api/load-all (if exists) ===")
la = post("/api/load-all", {})
print(json.dumps(la, indent=2, ensure_ascii=False)[:800])

print("\n=== POST /api/v12/orchestrate with sample ===")
orc = post("/api/v12/orchestrate", {"query": "System status and next recommended action", "context": {"mode": "synthesis"}})
print(json.dumps(orc, indent=2, ensure_ascii=False)[:1500])

print("\n=== POST /api/grok/chat (intent: status) ===")
chat = post("/api/grok/chat", {"message": "status", "mode": "intent"})
print(json.dumps(chat, indent=2, ensure_ascii=False)[:1000])

print("\n=== Agents use example (first agent) ===")
agents = get("/api/agents")
if "agents" in agents and agents["agents"]:
    first_id = agents["agents"][0]["id"]
    use = post(f"/api/agents/{first_id}/use", {"task": "Provide a short summary of current state."})
    print(f"Used agent {first_id}:", json.dumps(use, indent=2, ensure_ascii=False)[:600])
