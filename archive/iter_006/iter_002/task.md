## CRITICAL: Run Phase 3 Variance Diagnostic + Pooling Comparison

### Context
Phase 3 (iter_005) showed all spatiotemporal variants barely exceed untrained baseline (~42.85%) on 4-class classification. Code review confirms VICReg IS present in JEPALoss (λ_var=25, λ_cov=25). The pre-registration in src/pre_registration.md has been updated.

### Your ONLY task: Write and run a diagnostic script

Create `src/diagnostic_phase3_vicreg.py` and run it. The script must do the following:

**Part A: Train P3-C and measure per-epoch variance**

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
import numpy as np
import csv
import time

from spatiotemporal_dataset import generate_spatiotemporal_dataset, N_CLASSES
from spatiotemporal_encoder import SpatiotemporalEncoder
from training_objectives import JEPALoss, _Adam
from harness import SimpleLogisticRegression
from run_phase3 import (
    create_jepa_losses, reshape_for_spatial_jepa, reshape_spatial_grads_back,
    reshape_for_temporal_jepa, reshape_temporal_grads_back, train_jepa_epoch
)
```

Training config: P3-C, seed=42, d=16, d_out=16, 30 epochs, 200 train/class, 100 test/class, batch=64, lr=1e-3.

After each epoch (including epoch 0 before training starts), run the encoder forward on the TEST set and compute:
- Per-dim std of `fwd["pooled"]` (shape: n_test × 16 → compute std over rows for each of 16 dims)
- Per-dim std of each spatial layer output (flatten to 2D first: (N, d))
- Per-dim std of each temporal layer output
- Mean of the per-dim stds (one number per representation level)
- Also record the JEPA losses: spatial_loss, temporal_loss (from train_jepa_epoch return)

After the full training, also fit a logistic regression on the POOLED representation and report test accuracy.

**Part B: Untrained baseline variance**

Create an untrained P3-C encoder (same seed=42), run forward on test set, compute same variance metrics.

**Part C: Pooling comparison**

Using the TRAINED P3-C encoder from Part A, extract 4 different representations from the test set and train set, and fit a SimpleLogisticRegression for each:

1. **pooled**: `fwd["pooled"]` → shape (N, 16) — current method
2. **temporal_flat**: `fwd["temporal_outputs"][-1]` → shape (B, 26, 10, 16) → reshape to (N, 26*10*16) = (N, 4160). Since 4160 > 2000 features, first reduce with PCA to 100 dims (implement simple PCA with numpy: center data, compute top-100 eigenvectors of covariance, project).
3. **spatial_pooled_then_flat**: For each timestep, mean-pool over spatial → shape (B, 26, 16) → reshape to (N, 416)
4. **temporal_pooled_then_flat**: For each spatial position, mean-pool over temporal → shape (B, 10, 16) → reshape to (N, 160)

For each, report train_acc and test_acc.

**Part D: Save results**

Save epoch-level data to `src/variance_diagnostic_results.csv` with columns:
epoch, mean_pooled_std, mean_spatial_l0_std, mean_spatial_l1_std, mean_spatial_l2_std, mean_temporal_l0_std, mean_temporal_l1_std, mean_temporal_l2_std, spatial_loss, temporal_loss, train_acc, test_acc

Save pooling comparison to `src/pooling_comparison_results.csv` with columns:
representation, n_features, train_acc, test_acc

Also save untrained variance metrics separately (just print them).

**IMPORTANT**: Make the script self-contained and runnable. Use `python src/diagnostic_phase3_vicreg.py` to run it. It should complete within 20 minutes on CPU. The key insight we need is: (1) whether per-layer variance is ≥ 1.0 (VICReg working), (2) whether pooled variance is much lower (pooling destroys variance), (3) whether alternative pooling strategies give better classification.

Also write a brief analysis to `phase_3/diagnostic_report.md` summarizing findings.