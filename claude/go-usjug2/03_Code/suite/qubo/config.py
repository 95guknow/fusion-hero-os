import os

# QUBO Miner PoC Config
POOL_HOST = os.getenv("QUBO_POOL_HOST", "http://localhost:5000")
SOLVER_TYPE = os.getenv("QUBO_SOLVER", "neal")  # neal or gpu (later)
DEFAULT_DIFFICULTY = int(os.getenv("QUBO_DIFFICULTY", "60"))
NUM_READS_MULTIPLIER = int(os.getenv("QUBO_NUM_READS_MULT", "20"))

# Integration
USE_VRAM_CACHE = os.getenv("FUSION_USE_VRAM", "1") == "1"
USE_SSD_CACHE = os.getenv("FUSION_USE_SSD", "1") == "1"

# Core Pinning (siehe core_pinning.py)
PIN_CORES = list(range(int(os.getenv("QUBO_PIN_CORES", "12"))))
