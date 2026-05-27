"""
Background launcher for Phase 3 parallel experiments.
Runs the full suite and logs output.
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from run_phase3_parallel import main

if __name__ == "__main__":
    main()
