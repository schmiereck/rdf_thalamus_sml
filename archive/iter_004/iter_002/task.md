## Run P2-A, P2-B, P2-C Baselines for Phase 2

Run the three temporal encoder baselines using the existing infrastructure. All must use JEPA as the training objective.

### What Already Exists
- `src/temporal_dataset.py` — `generate_temporal_dataset()` and `generate_irregular_markov_dataset()`
- `src/temporal_encoder.py` — P2DEncoder, P2AEncoder, P2BEncoder, P2CEncoder
- `src/training_objectives.py` — JEPALoss, _Adam
- `src/harness.py` — SimpleLogisticRegression
- `src/run_phase2.py` — reference for training loop and evaluation

### Task: Create and run `src/run_phase2_baselines.py`

This script should train P2-A, P2-B, P2-C encoders on temporal data with JEPA, evaluate them, and save results.

#### Configuration
- d=16, d_out=16 for all encoders
- 5 seeds: [42, 43, 44, 45, 46]
- 200 epochs each
- lr=1e-3, batch_size=32
- Same datasets as P2-D experiments

#### Training Loop Pattern (for each encoder type)

The general pattern is:
```
for epoch in range(200):
    codes = encoder.forward(train_emb)    # (B, T, d_out)
    result = jepa.step([codes])            # updates JEPA predictors
    code_grads = result["code_grads"][0]   # (B, T, d_out)
    enc_grads = encoder.compute_gradients(train_emb, code_grads)
    adam.step(encoder_params, encoder_grads)
```

**For P2-B (recurrent RNN):** It already has `compute_gradients(x, dL_dcodes)` that returns `{"W_xh", "W_hh", "b_h", "x"}`. Use _Adam on `{"W_xh": encoder.W_xh, "W_hh": encoder.W_hh, "b_h": encoder.b_h}`.

**For P2-C (output feedback):** It already has `compute_gradients(x, dL_dcodes)` that returns `{"W_enc", "b_enc", "W_proj", "x"}`. Use _Adam on `{"W_enc": encoder.node.W_enc, "b_enc": encoder.node.b_enc, "W_proj": encoder.W_proj}`.

**For P2-A (multi-tick):** It does NOT have `compute_gradients`. You need to add one to the P2AEncoder class in `src/temporal_encoder.py`. Here's how:

The P2-A forward does:
1. Pad x to multiple of N
2. Reshape to (B, n_blocks, N, d)
3. Average-pool over N: pooled = blocks.mean(axis=2) → (B, n_blocks, d)
4. Expand back: pooled_3d = repeat pooled over N → (B*n_blocks, N, d) — this becomes the 3-slot input
5. Forward through UniversalNode: codes = node.forward(pooled_3d)
6. Repeat codes back to full T length

For compute_gradients:
1. Take dL_dcodes of shape (B, T, d_out)
2. Pad and reshape to (B, n_blocks, N, d_out) → sum over N → (B, n_blocks, d_out) → reshape to (B*n_blocks, d_out)
3. Backprop through node: dL_dz = dL_dcodes_flat * (1 - codes^2); dW_enc = pooled_3d_flat.T @ dL_dz / batch; db_enc = dL_dz.mean(0)
4. Where pooled_3d_flat is the flattened (B*n_blocks, 3*d) input to the node

Return `{"W_enc": dW_enc, "b_enc": db_enc}`. Only need gradients for the node parameters since the pooling is fixed (no learnable parameters).

Then use _Adam on `{"W_enc": encoder.node.W_enc, "b_enc": encoder.node.b_enc}`.

#### Evaluation (same as P2-D)

For each trained encoder:
1. **Classification**: codes = encoder.forward(test_emb); mean_pool over time; SimpleLogisticRegression probe (3 classes, 16 features)
2. **Next-step prediction (Markov)**: Ridge regression from codes[:-1] to embeddings[1:], measure mean cosine similarity
3. **JEPA loss**: Final loss after training

#### Output

Save to `phase_2/baseline_results.csv` with columns:
- config, seed, test_accuracy, train_accuracy, next_step_cosine_markov, next_step_cosine_classification, final_jepa_loss

#### Also Save Untrained P2-A, P2-B, P2-C Baselines

For each encoder type, also run an untrained baseline (random weights, freeze encoder, only train JEPA predictor for 200 epochs). This gives us untrained baselines for F3 comparison. Save these with config names "P2-A-Untrained", "P2-B-Untrained", "P2-C-Untrained".

So total configs: P2-A-Trained, P2-B-Trained, P2-C-Trained, P2-A-Untrained, P2-B-Untrained, P2-C-Untrained = 6 configs × 5 seeds = 30 runs.

#### CRITICAL: Run the script and save results

After creating the script, RUN IT to completion. Save results to phase_2/baseline_results.csv. Print the summary at the end.
