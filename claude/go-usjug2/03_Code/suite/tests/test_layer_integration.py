#!/usr/bin/env python3
"""Tests for layer integrations with ghosthunt hook."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_qubo_layer_hook():
    """Test that qubo layer integrates ghost state."""
    # Run the layer script which includes the hook
    import subprocess
    import os
    result = subprocess.run([sys.executable, 'layers/02_qubo/qubo_layer.py'], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assert result.returncode == 0
    assert 'QUBO Layer' in result.stdout
    print("test_qubo_layer_hook: PASS (script runs with hook)")

def test_gpu_layer_hook():
    """Test gpu layer hook integration."""
    import subprocess
    import os
    result = subprocess.run([sys.executable, 'layers/03_gpu/gpu_layer.py'], capture_output=True, text=True, cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    assert result.returncode == 0
    assert 'GPU Layer' in result.stdout
    print("test_gpu_layer_hook: PASS (script runs with hook)")

if __name__ == "__main__":
    test_qubo_layer_hook()
    test_gpu_layer_hook()
