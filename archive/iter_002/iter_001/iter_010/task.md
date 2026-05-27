Write a script `test_scale.py` to evaluate the effect of embedding initialization scale on the performance of `HierarchicalEncoder`.
Try different initialization methods for `self.embedding` in `HierarchicalEncoder`:
1. Uniform in `[-0.01, 0.01]` (current)
2. Uniform in `[-0.1, 0.1]`
3. Uniform in `[-1.0, 1.0]`
4. Standard normal (mean 0, std 1)
5. Normal with std 0.5

For each method, instantiate a `HierarchicalEncoder` with `sharing_mode='cross_layer', d=8, l1_lambda=0.002, seed=42`, train it for 50 epochs per layer on the Phase 1 dataset, and evaluate:
- test accuracy
- train accuracy
- code sparsity (threshold 1e-3)
- average code magnitude (mean(|code|))
- untrained baseline test accuracy for the same embedding initialization.

Print the comparison table. This will show us how to prevent the representation collapse and achieve the scientific success criteria of Phase 1! Run the script and return the results.