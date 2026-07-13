# QUBO Optimization for ASR Turn-Taking

**Problem:** Dynamic optimization of VAD threshold, pause tolerance, and prosody weighting for disfluent speech.

**Variables (QUBO):**
- x1 = VAD energy threshold
- x2 = Pause duration tolerance
- x3 = Filler word penalty weight
- x4 = Intonation rise detection sensitivity

**Fitness Function:**
Number of correct turn-ends on real recordings with heavy äh/pause usage minus false breaks.

**Goal:** Evolve parameters over 10,000+ generations using classical or quantum-inspired solvers.

This module runs continuously in background to keep ASR calibrated to the user's natural speaking style.