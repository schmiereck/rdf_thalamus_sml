Please execute Phase 2 of the HSUN project: Temporal Integration at a Single Node.

### Context and Objectives
You need to implement the temporal integration infrastructure and execute the P2-D experiments to test if the spatial-trained UniversalNode transfers successfully to the temporal axis.

Follow the exact instructions in the user prompt to build:
1. `src/pre_registration.md` (Update)
2. `src/temporal_dataset.py` (Create)
3. `src/temporal_encoder.py` (Create)
4. `src/run_phase2.py` (Create)
5. `src/test_temporal.py` (Create)
6. Run the experiments over 5 seeds (42-46) and output results to `phase_2/p2d_results.csv`.

### Specific Technical Guidelines:

1. **Pre-registration update**: Add F0 at the very top of Falsification Criterion. Keep F1, F2, F3.
2. **State embeddings**: Generated using Xavier-scaled standard normal scaled by `sqrt(2.0/d)`. E.g., `rng.standard_normal((8, 16)) * np.sqrt(2.0 / 16.0)`.
3. **Dataset**: Create 200 train / 100 test sequences per category (length 64, d=16). Separate held-out irregular Markov chain dataset for next-step prediction (200 train, 100 test).
4. **Encoders**:
   - `P2DEncoder`: Use `UniversalNode`. Accepts `(B, T, d)`. Generate sliding window triplets of shape `(B, T-2, 3, d)`. Feed to node to produce `(B * (T-2), d_out)`. Reshape to `(B, T-2, d_out)` and pad at the beginning with 2 steps of zeros to yield shape `(B, T, d_out)`.
   - `P2AEncoder`: Average pool non-overlapping blocks of N=3 steps. Receive `(p_{k-2}, p_{k-1}, p_k)` as 3-slot input. Repeat code over block steps to match shape `(B, T, d_out)`.
   - `P2BEncoder`: Hidden state of dim d_out = d. Recurrent RNN update `h = tanh(x_t @ W_xh + h @ W_hh + b_h)`.
   - `P2CEncoder`: Feedback previous code to 3-slot input: `(code_{t-1}, embedding_{t-1}, embedding_t)`.
5. **Loss**: Use `JEPALoss(n_layers=1, d=d_out)` from `src/training_objectives.py` for time-axis codes. Note that calling `.step([codes])` on the sequence codes (shape `(B, T, d_out)`) trains the predictors of the JEPA loss and returns predictor gradients and `"code_grads"`.
6. **Config 1 (Zero-Shot)**: Train spatial Phase-1 JEPA-d16 HierarchicalEncoder for 200 epochs first. Load its master node's `W_enc` and `b_enc`. Freeze these weights in `P2DEncoder`. Train only the JEPALoss predictor on the temporal sequences for 200 epochs.
7. **Config 2 (Temporal Training)**: Train P2-D from scratch for 200 epochs. Backprop the JEPALoss `"code_grads"` through the temporal node's encoder. Update `W_enc` and `b_enc` using Adam (`_Adam` class from `src/training_objectives.py`).
8. **Config 3 (Untrained Baseline)**: Untrained random `UniversalNode` (frozen weights). Train only JEPALoss predictor on temporal sequences for 200 epochs.
9. **Linear Probe for Classification**: Train `SimpleLogisticRegression` (3 classes) on sequence mean codes on training set, evaluate on test set.
10. **Next-Step Prediction**: Fit Ridge regression or least-squares linear projection from code `z_t` to `embedding_{t+1}` on training triplets. Compute mean cosine similarity of predicted vs actual on test sequences.

Save all results to `phase_2/p2d_results.csv`. Create self-tests in `src/test_temporal.py` and run them first to ensure everything works perfectly. Write clean, modular, and extremely robust code! Use only numpy and scipy (no torch, no tensorflow). Ensure to save results correctly. Let's do this!