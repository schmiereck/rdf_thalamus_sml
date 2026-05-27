"""Medium test for Phase 3: 20 epochs, 3 seeds, all variants."""
import sys
sys.path.insert(0, 'src')
from run_phase3 import main

# Override globals
import run_phase3 as r
r.EPOCHS = 20
r.SEEDS = [42, 43, 44]
r.RESULTS_CSV = "phase_3/phase3_results_medium.csv"
r.SHORTCUT_CSV = "phase_3/shortcut_baselines_medium.csv"

main(smoke_test=False)
