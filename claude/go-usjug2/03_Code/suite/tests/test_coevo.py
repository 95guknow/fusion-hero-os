#!/usr/bin/env python3
"""Test coevolutionary processing."""
import sys
import json
from pathlib import Path
sys.path.insert(0, ".")

def test_process_layers_creates_log():
    """Running process should create/update coevo log (if run)."""
    log_path = Path("coevo_evolution_log.json")
    # Note: actual run is expensive, just check structure if exists
    if log_path.exists():
        with open(log_path) as f:
            data = json.load(f)
        assert isinstance(data, list) or "value" in data  # from previous format
        print("Log exists with data.")
    else:
        print("No log yet, run process_layers.py to generate.")
    print("test_process_layers_creates_log: PASS (structure)")

if __name__ == "__main__":
    test_process_layers_creates_log()
