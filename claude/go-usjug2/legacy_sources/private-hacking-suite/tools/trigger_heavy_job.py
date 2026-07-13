import os
import time
import requests
import json

# Ensure flags
os.environ['FUSION_USE_GPU'] = '1'
os.environ['FUSION_VIRTUAL_HT_GPU'] = '1'
os.environ['FUSION_VIRTUAL_THREADS'] = '64'

print("Triggering heavy job (private suite)...")

# Try to trigger via input layer a heavy QUBO
try:
    payload = {
        "intent": "qubo",
        "params": {
            "size": 128,
            "steps": 8000,
            "n_restarts": 16,
            "T0": 3.0,
            "parallel": True,
            "use_gpu": True,
            "virtual_ht": True
        }
    }
    r = requests.post("http://127.0.0.1:8000/api/input", json=payload, timeout=10)
    print("Input response:", r.status_code, r.text[:200] if r.text else "")
    job_id = None
    if r.ok:
        data = r.json()
        job_id = data.get("job_id")
        print("Job ID:", job_id)
except Exception as e:
    print("Input trigger failed:", e)

# Fallback / also trigger benchmark for heavy parallel load
try:
    payload2 = {"message": "heavy benchmark with large QUBO n=128, max steps, GPU + virtual HT", "mode": "full"}
    r2 = requests.post("http://127.0.0.1:8000/api/grok/chat", json=payload2, timeout=10)
    print("Grok chat response:", r2.status_code)
except Exception as e:
    print("Grok trigger failed:", e)

# If we have a job, poll a bit
if job_id:
    for i in range(5):
        time.sleep(2)
        try:
            rj = requests.get(f"http://127.0.0.1:8000/api/jobs/{job_id}", timeout=5)
            print(f"Job poll {i+1}:", rj.text[:150])
        except:
            pass

print("Heavy job triggered. Watch nvidia-smi and the workspace.")
print("To monitor: nvidia-smi -l 1")
