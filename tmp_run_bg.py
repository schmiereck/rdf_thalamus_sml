"""
Phase 1 Experiment Runner — Background execution wrapper.
Slices the 30 runs into chunks to avoid console timeout.
"""
import os
os.environ['PYTHONUNBUFFERED'] = '1'

import sys
sys.stdout = open('phase_1/run_progress.txt', 'w', buffering=1)

# Now delegate to the real runner
import runpy
runpy.run_module('src.run_phase1', run_name='__main__')
