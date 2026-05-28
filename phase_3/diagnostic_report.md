# Phase 3 Variance Diagnostic & Pooling Comparison Report

## Configuration

- **Variant**: P3-C (single shared master node)
- **Seed**: 42
- **Dimensions**: d=16, d_out=16
- **Training**: 30 epochs, 200 train/class, 100 test/class, batch=64, lr=0.001
- **JEPA alpha**: 0.5 (joint spatial + temporal)

## Part A/B: Per-Epoch Variance (Trained vs Untrained)

| Representation | Init (Epoch 0) | After 30 Epochs | Change |
|----------------|---------------|-----------------|--------|
| pooled         |        0.0339 |          0.0753 | +0.0415 |
| spatial_l0     |        0.1178 |          0.2980 | +0.1803 |
| spatial_l1     |        0.1425 |          0.5204 | +0.3779 |
| spatial_l2     |        0.1633 |          0.6458 | +0.4825 |
| temporal_l0    |        0.1914 |          0.7176 | +0.5262 |
| temporal_l1    |        0.2167 |          0.7404 | +0.5237 |
| temporal_l2    |        0.2443 |          0.7515 | +0.5072 |

### Untrained Baseline (separate fresh init)

- **pooled**: 0.0339
- **spatial_l0**: 0.1178
- **spatial_l1**: 0.1425
- **spatial_l2**: 0.1633
- **temporal_l0**: 0.1914
- **temporal_l1**: 0.2167
- **temporal_l2**: 0.2443

## Part C: Pooling Comparison

| Representation          | N Features | Train Acc | Test Acc |
|-------------------------|-----------:|----------:|---------:|
| pooled                  |         16 |    0.4450 |   0.4425 |
| temporal_flat_pca100    |        100 |    0.5913 |   0.4100 |
| spatial_pooled_then_flat |        416 |    0.8512 |   0.5350 |
| temporal_pooled_then_flat |        160 |    0.6300 |   0.4900 |

## Key Findings & Interpretation

### 1. VICReg Variance Dynamics

**Warning**: Some layers fell below std = 1.0 despite VICReg. This suggests the variance penalty may be insufficiently strong or is competing with other gradient components (e.g., JEPA prediction loss, L1, or the covariance term).

- **Pooled representation**: std moved from **0.0339** at init to **0.0753** after training.
  The pooled std is well below 1.0, indicating that **mean-pooling across all spatial and temporal positions collapses the representation diversity** that VICReg preserved at the layer level. This is a critical bottleneck:
  the encoder learns rich hidden codes, but the pooling operation averages them away, leaving a near-constant vector that carries little class-discriminative information.

### 2. Layer-wise Variance Trajectory

