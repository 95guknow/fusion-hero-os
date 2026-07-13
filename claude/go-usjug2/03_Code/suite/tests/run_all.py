#!/usr/bin/env python3
"""Run all tests in the suite."""
import subprocess
import sys
from pathlib import Path

tests_dir = Path(__file__).parent
print("Running all tests...")

tests = [
    "test_springloop.py",
    "test_ghosthunt_hook.py",
    "test_coevo.py",
    "test_layer_integration.py",
    "test_middle_out.py",
]

for t in tests:
    print(f"\n=== {t} ===")
    try:
        result = subprocess.run([sys.executable, str(tests_dir / t)], capture_output=True, text=True, timeout=30)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr[:200])
        if result.returncode != 0:
            print("FAILED")
    except Exception as e:
        print(f"Error: {e}")

print("\nAll tests attempted.")