import llama_cpp
print("llama_cpp version ok")
print([x for x in dir(llama_cpp) if "lora" in x.lower() or "LoRA" in x])