#!/usr/bin/env python3
"""
Layer 3: LLM / Internal Models (Private)
"""
print("[Layer 3] LLM Layer - see llm/ for backends, optimizer, train")
print("Springloop can optimize training params or QUBO-sample selection.")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Hook ghosthunting coevolutionär, use state to 'tune' LLM params metaphorically
try:
    from ghosthunting.hook import ghosthunt_hook
    snap, coevo = ghosthunt_hook("04_llm", context={"events": 12}, use_springloop=True)
    if coevo and coevo.get('emerged', 0) > 0:
        print(f"  Adjusted LLM ctx based on ghosts: +{coevo['emerged']*8}")
except Exception as e:
    print(f"  Ghosthunt hook failed: {e}")
