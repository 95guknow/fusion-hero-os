#!/usr/bin/env python3
"""Test for middle_out expression."""
import sys
import os
import subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_middle_out_runs():
    """middle_out should run without error and print middle-out."""
    result = subprocess.run([sys.executable, 'layers/00_middle/middle_out.py'], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assert result.returncode == 0
    assert 'MIDDLE-OUT' in result.stdout or 'middleout' in result.stdout.lower()
    print("test_middle_out_runs: PASS")

if __name__ == "__main__":
    test_middle_out_runs()
