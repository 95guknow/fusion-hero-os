import urllib.request
import json

print("=== Workspace Check ===")
try:
    r = urllib.request.urlopen("http://127.0.0.1:8080", timeout=5)
    print("Workspace root status:", r.getcode())
    content = r.read().decode()[:200]
    print("Sample:", repr(content))
except Exception as e:
    print("Workspace DOWN:", str(e)[:100])

print("\n=== GUI Status ===")
try:
    r = urllib.request.urlopen("http://127.0.0.1:8000/api/gui/status", timeout=5)
    data = json.loads(r.read().decode())
    print(json.dumps(data, indent=2))
except Exception as e:
    print("GUI error:", str(e)[:100])

print("\n=== Full Health Summary ===")
try:
    r = urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=5)
    data = json.loads(r.read().decode())
    print("backend:", data.get("backend"))
    print("mainframe.loaded:", data.get("mainframe", {}).get("loaded"))
    print("grok_intern_aligned:", data.get("v12", {}).get("grok_intern_aligned"))
    reg = data.get("registry", {}).get("summary", {})
    print("modules:", reg.get("loaded"), "/", reg.get("total_modules"))
    print("agents:", reg.get("total_agents"))
    print("all_ok:", reg.get("all_ok"))
    print("hyperthreading:", data.get("hyperthreading", {}).get("enabled"))
except Exception as e:
    print("Health error:", e)
