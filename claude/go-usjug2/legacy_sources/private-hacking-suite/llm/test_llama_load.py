import sys
from pathlib import Path

model = Path("models/Llama-3.2-1B-Instruct-Q4_K_M.gguf")
print("model exists", model.exists(), model.stat().st_size if model.exists() else 0)

try:
    from llama_cpp import Llama
    llm = Llama(model_path=str(model), n_ctx=512, n_gpu_layers=0, verbose=False)
    print("llama_cpp ok", llm("Hello", max_tokens=5))
except Exception as e:
    print("llama_cpp fail", type(e).__name__, e)
    sys.exit(1)