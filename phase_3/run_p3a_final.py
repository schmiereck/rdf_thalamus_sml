import sys, os, time, csv
sys.path.insert(0, 'src')
from run_phase3_optimized import run_single_experiment_opt, save_result_incrementally, N_TRAIN_PER_CLASS, N_TEST_PER_CLASS, EPOCHS, BATCH_SIZE, LR

RESULTS_CSV = "phase_3/phase3_full_results.csv"

for seed in [45, 46]:
    print(f"\n=== P3-A seed={seed} ===")
    t0 = time.time()
    result = run_single_experiment_opt(
        variant="P3-A",
        seed=seed,
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        lr=LR,
        update_encoder=True,
        n_train_per_class=N_TRAIN_PER_CLASS,
        n_test_per_class=N_TEST_PER_CLASS,
    )
    save_result_incrementally(result, RESULTS_CSV)
    t1 = time.time()
    print(f"  Done in {t1-t0:.1f}s. Test acc: {result['test_acc']:.4f}")

print("\nAll P3-A runs complete!")
