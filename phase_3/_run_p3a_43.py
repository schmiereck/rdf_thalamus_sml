"""Run a single P3-A experiment."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, 'src')

from run_phase3_optimized import (
    run_single_experiment_opt,
    save_result_incrementally,
    EPOCHS, BATCH_SIZE, LR,
    N_TRAIN_PER_CLASS, N_TEST_PER_CLASS,
)

seed = 43
print(f"Running P3-A, seed={seed}...")
result = run_single_experiment_opt(
    variant='P3-A',
    seed=seed,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    lr=LR,
    update_encoder=True,
    n_train_per_class=N_TRAIN_PER_CLASS,
    n_test_per_class=N_TEST_PER_CLASS,
)
save_result_incrementally(result, 'phase_3/phase3_full_results.csv')
print(f"Done. test_acc={result['test_acc']:.4f}")
