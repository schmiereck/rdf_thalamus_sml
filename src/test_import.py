import sys, os
sys.path.insert(0, os.path.dirname(__file__))

print("Importing...")
from run_phase3 import run_single_experiment
print("Imported successfully")

# Try a tiny smoke test
print("Running smoke test (2 epochs)...")
result = run_single_experiment(variant="P3-B", seed=43, epochs=2, batch_size=32, lr=1e-3)
print(f"Done! test_acc={result['test_acc']:.4f}")
